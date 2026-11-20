"""Servidor local de Lincoyán sin Node.

Sirve public/ e imita las rutas de la API que la web usa para leer y guardar, con los datos
en un archivo JSON local. Sirve para probar el front en un equipo sin wrangler.

1. GET /api/state entrega los días y las colecciones del archivo de datos.
2. PUT /api/days/:fecha y PUT /api/lib/:clave guardan en el archivo.
3. POST /api/import reemplaza las claves que trae.
4. GET /api/precio?q= busca precios de referencia en Unimarc, igual que src/precios.js.
5. El resto de /api responde 404 (modelo, finanzas, push, reloj).

Uso:
    python tools/local/servidor.py                       # http://localhost:8787
    python tools/local/servidor.py --importar lincoyan-2026-11-20.json
    python tools/local/servidor.py --puerto 9000 --datos otra-ruta.json

Datos: tools/local/datos.json por defecto (ignorado por git).
"""

import argparse
import json
import re
import threading
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PUBLICO = RAIZ / "public"
LIB_KEYS = {"goals", "profile", "techniques", "songs", "books", "coach", "foods", "combos", "share", "optim", "fin", "prices", "tabs"}
CANDADO = threading.Lock()
VTEX_SEARCH = "https://unimarc.vtexcommercestable.com.br/api/catalog_system/pub/products/search"
PRODUCT_URL = "https://www.unimarc.cl/product/"
SIZE_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*(kg|kilo|gr|g|lt|l|ml|cc)\b", re.I)


def leer(ruta):
    if not ruta.exists():
        return {"days": {}, "lib": {}}
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return {"days": datos.get("days", {}), "lib": datos.get("lib", {})}


def escribir(ruta, datos):
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    tmp.replace(ruta)


def importar(ruta, archivo):
    """Carga una exportación de la app (Perfil → Exportar) como datos locales."""
    exp = json.loads(Path(archivo).read_text(encoding="utf-8"))
    datos = leer(ruta)
    datos["days"].update(exp.get("days", {}))
    for clave, valor in (exp.get("lib") or {}).items():
        if clave in LIB_KEYS:
            datos["lib"][clave] = envolver(clave, valor)
    escribir(ruta, datos)
    return len(exp.get("days", {})), len(exp.get("lib") or {})


def envolver(clave, valor):
    """Las colecciones se guardan con su envoltura ({list: …}, {values: …}, {reviews: …})."""
    if isinstance(valor, dict) and any(k in valor for k in ("list", "values", "reviews")):
        return valor
    if clave == "coach":
        return {"reviews": valor}
    return {"list": valor} if isinstance(valor, list) else {"values": valor}


def precio_unitario(p):
    """Precio por kg, litro o unidad de un producto del catálogo (copia de unitPrice() en src/precios.js)."""
    item = (p.get("items") or [{}])[0]
    oferta = ((item.get("sellers") or [{}])[0]).get("commertialOffer") or {}
    precio = float(oferta.get("Price") or 0)
    if precio <= 0 or oferta.get("IsAvailable") is False:
        return None
    try:
        pd = json.loads((p.get("ProductData") or ["{}"])[0] or "{}")
    except ValueError:
        pd = {}
    mu, qty = str(pd.get("measurement_unit_un") or "").lower(), float(pd.get("unit_multiplier_un") or 0)
    if str(item.get("measurementUnit") or "").lower() == "kg":
        return precio, "kg", precio, float(item.get("unitMultiplier") or 1)
    if mu == "kg" and qty > 0:
        return precio, "kg", precio / qty, qty
    if mu in ("litro", "lt", "l") and qty > 0:
        return precio, "L", precio / qty, qty
    if mu == "unidad" and qty > 0:
        return precio, "un", precio / qty, qty
    m = SIZE_RE.search(p.get("productName") or "")
    if m:
        v, u = float(m.group(1).replace(",", ".")), m.group(2).lower()
        per, q = ("kg", v) if u in ("kg", "kilo") else ("L", v) if u in ("lt", "l") else ("L", v / 1000) if u in ("ml", "cc") else ("kg", v / 1000)
        if q > 0:
            return precio, per, precio / q, q
    return precio, "un", precio, 1


def buscar_unimarc(q):
    """Busca en el catálogo público de Unimarc y devuelve los productos como parseUnimarc() de src/precios.js."""
    url = f"{VTEX_SEARCH}?ft={urllib.parse.quote(q)}&_from=0&_to=19"
    req = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": "Mozilla/5.0 (compatible; Lincoyan/1.0)"})
    with urllib.request.urlopen(req, timeout=20) as r:
        lista = json.loads(r.read().decode("utf-8"))
    items = []
    for p in lista if isinstance(lista, list) else []:
        u = precio_unitario(p)
        if not u or not p.get("productName") or not p.get("linkText"):
            continue
        oferta = ((((p.get("items") or [{}])[0]).get("sellers") or [{}])[0]).get("commertialOffer") or {}
        items.append({"name": " ".join(p["productName"].split()), "brand": p.get("brand") or "", "cat": (p.get("categories") or [""])[0],
                      "url": PRODUCT_URL + p["linkText"], "price": round(u[0]), "listPrice": round(float(oferta.get("ListPrice") or u[0])),
                      "per": u[1], "unitPrice": round(u[2]), "qty": u[3]})
    return items


class Manejador(SimpleHTTPRequestHandler):
    datos_ruta: Path

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLICO), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, formato, *args):
        if not self.path.startswith("/api/"):
            return
        super().log_message(formato, *args)

    def responder(self, codigo, cuerpo):
        datos = json.dumps(cuerpo, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def cuerpo(self):
        largo = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(largo) or b"null")

    def do_GET(self):
        ruta = self.path.split("?")[0]
        if ruta == "/api/state":
            with CANDADO:
                datos = leer(self.datos_ruta)
            dias = dict(sorted(datos["days"].items(), reverse=True)[:400])
            return self.responder(200, {"days": dias, "lib": datos["lib"], "movs": [], "movDet": {}})
        if ruta == "/api/precio":
            q = (urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get("q") or [""])[0].strip().lower()[:80]
            if len(q) < 2:
                return self.responder(400, {"error": "bad_query"})
            try:
                return self.responder(200, {"q": q, "source": "unimarc", "items": buscar_unimarc(q)})
            except OSError as err:
                return self.responder(502, {"error": "upstream", "detail": str(err)[:200]})
        if ruta.startswith("/api/"):
            return self.responder(404, {"error": "no disponible en el servidor local"})
        if ruta.startswith("/s/"):
            self.path = "/index.html"
        return super().do_GET()

    def do_PUT(self):
        ruta = self.path.split("?")[0]
        dia = re.fullmatch(r"/api/days/(\d{4}-\d{2}-\d{2})", ruta)
        lib = re.fullmatch(r"/api/lib/([a-z]+)", ruta)
        if not dia and not (lib and lib.group(1) in LIB_KEYS):
            return self.responder(404, {"error": "unknown_key"})
        doc = self.cuerpo()
        with CANDADO:
            datos = leer(self.datos_ruta)
            if dia:
                datos["days"][dia.group(1)] = doc
            else:
                datos["lib"][lib.group(1)] = doc
            escribir(self.datos_ruta, datos)
        return self.responder(200, {"ok": True})

    def do_POST(self):
        ruta = self.path.split("?")[0]
        if ruta != "/api/import":
            return self.responder(404, {"error": "no disponible en el servidor local"})
        doc = self.cuerpo() or {}
        with CANDADO:
            datos = leer(self.datos_ruta)
            datos["days"].update(doc.get("days") or {})
            for clave, valor in (doc.get("lib") or {}).items():
                if clave in LIB_KEYS:
                    datos["lib"][clave] = envolver(clave, valor)
            escribir(self.datos_ruta, datos)
        return self.responder(200, {"ok": True})


def main():
    p = argparse.ArgumentParser(description="Servidor local de Lincoyán sin Node")
    p.add_argument("--puerto", type=int, default=8787)
    p.add_argument("--datos", type=Path, default=Path(__file__).with_name("datos.json"))
    p.add_argument("--importar", help="exportación JSON de la app para cargar como datos locales")
    a = p.parse_args()
    if a.importar:
        dias, libs = importar(a.datos, a.importar)
        print(f"Importé {dias} días y {libs} colecciones en {a.datos}")
    Manejador.datos_ruta = a.datos
    servidor = ThreadingHTTPServer(("127.0.0.1", a.puerto), Manejador)
    print(f"Lincoyán local en http://localhost:{a.puerto} (datos en {a.datos}). Ctrl+C para detener.")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
