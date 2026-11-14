"""Cartolas de BICE a Lincoyán.

Abre el sitio de BICE en un navegador local; el titular ingresa y aprueba con BICE Pass. Cada cartola
que se descarga en esa ventana se sube a la app (POST /api/cartola) y se borra del disco.

1. Abre Chrome con un perfil propio en tools/bice/.perfil.
2. Espera las descargas de la sesión y sube cada archivo a la app con el service token de Access.
3. Registra en recorrido.jsonl las páginas visitadas y los clics, sin números de cuenta ni montos.
4. Termina al cerrar la ventana del navegador.

Uso:
    python cartolas.py --configurar      guarda el service token en el Administrador de credenciales
    python cartolas.py                   abre BICE y sube las cartolas que descargues
    python cartolas.py --archivo X.csv   sube un archivo sin abrir el navegador
    python cartolas.py --guardar         conserva los CSV descargados en tools/bice/descargas

Requisitos: pip install -r requirements.txt y patchright install chrome.
Variables de entorno: LINCOYAN_URL (por defecto https://tracker.yerkolincoyan.cl).
"""

import argparse
import getpass
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import keyring

AQUI = Path(__file__).resolve().parent
PERFIL = AQUI / ".perfil"
DESCARGAS = AQUI / "descargas"
RECORRIDO = AQUI / "recorrido.jsonl"
APP = os.environ.get("LINCOYAN_URL", "https://tracker.yerkolincoyan.cl").rstrip("/")
INICIO = "https://www.bice.cl"
SERVICIO = "lincoyan-cartolas"

CLICS_JS = """
(() => {
  const limpio = s => String(s || "").replace(/\\s+/g, " ").trim().slice(0, 80);
  document.addEventListener("click", e => {
    const el = e.target.closest("a,button,[role=button],[role=tab],[role=menuitem],input[type=submit],li,span,div");
    if (!el || !window.lincoyanClic) return;
    window.lincoyanClic({
      tag: el.tagName.toLowerCase(), texto: limpio(el.innerText || el.value), id: el.id || "",
      clases: limpio(el.className && el.className.baseVal === undefined ? el.className : ""),
      aria: limpio(el.getAttribute("aria-label")), href: limpio(el.getAttribute("href")),
    });
  }, true);
})();
"""


def anonimo(texto):
    """Texto sin números largos (cuentas, montos, RUT) ni correos."""
    texto = re.sub(r"[\w.+-]+@[\w-]+\.[\w.]+", "<correo>", str(texto))
    texto = re.sub(r"\$\s*\d[\d.,]*", "$####", texto)
    return re.sub(r"\d[\d.\-]{3,}", "####", texto)


def registrar(evento):
    """Agrega un evento anónimo a recorrido.jsonl."""
    limpio = {k: anonimo(v) for k, v in evento.items()}
    limpio["t"] = datetime.now().strftime("%H:%M:%S")
    with RECORRIDO.open("a", encoding="utf-8") as f:
        f.write(json.dumps(limpio, ensure_ascii=False) + "\n")


def credenciales():
    """Client ID y secreto del service token desde el Administrador de credenciales."""
    cid = keyring.get_password(SERVICIO, "client_id")
    sec = keyring.get_password(SERVICIO, "client_secret")
    if not cid or not sec:
        sys.exit("Falta el service token. Ejecuta: python cartolas.py --configurar")
    return cid, sec


def configurar():
    """Guarda el service token de Access en el Administrador de credenciales de Windows."""
    cid = input("Client ID del service token: ").strip()
    sec = getpass.getpass("Client Secret (no se muestra): ").strip()
    if not cid or not sec:
        sys.exit("Faltan datos; no se guardó nada.")
    keyring.set_password(SERVICIO, "client_id", cid)
    keyring.set_password(SERVICIO, "client_secret", sec)
    print("Service token guardado.")


def texto_csv(ruta):
    """Contenido del CSV en UTF-8 o, si no lo es, en Windows-1252."""
    datos = Path(ruta).read_bytes()
    try:
        return datos.decode("utf-8")
    except UnicodeDecodeError:
        return datos.decode("cp1252")


def resumen(r):
    """Frase con el resultado de la importación."""
    if r.get("tipo") == "cuenta":
        base = f"cuenta: {r.get('filas', 0)} movimientos, {r.get('nuevos', 0)} nuevos, {r.get('conciliados', 0)} unidos a alertas o correos"
    else:
        base = f"crédito: {r.get('filas', 0)} filas, {r.get('nuevos', 0)} nuevas, {r.get('conciliados', 0)} unidas a alertas"
    cuadra = {True: "los cargos cuadran con el total", False: "los cargos NO cuadran con el total", None: ""}[r.get("cuadra")]
    raros = r.get("desconocidos") or []
    return "; ".join(x for x in [base, cuadra, f"sin reconocer: {' · '.join(raros)}" if raros else ""] if x)


def subir(ruta):
    """Sube un CSV a /api/cartola; devuelve True si la app lo importó."""
    cid, sec = credenciales()
    req = urllib.request.Request(
        f"{APP}/api/cartola", data=texto_csv(ruta).encode("utf-8"), method="POST",
        headers={"content-type": "text/csv; charset=utf-8", "CF-Access-Client-Id": cid, "CF-Access-Client-Secret": sec},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            r = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        motivo = e.read().decode("utf-8", "replace")[:200]
        print(f"  {Path(ruta).name}: la app respondió {e.code} ({motivo})")
        return False
    except urllib.error.URLError as e:
        print(f"  {Path(ruta).name}: sin conexión con la app ({e.reason})")
        return False
    print(f"  {Path(ruta).name}: {resumen(r)}")
    return True


def navegar(guardar):
    """Abre BICE, sube cada descarga y registra el recorrido hasta que se cierra la ventana."""
    from patchright.sync_api import sync_playwright

    credenciales()
    DESCARGAS.mkdir(exist_ok=True)
    registrar({"evento": "inicio"})
    subidas = []

    def al_descargar(descarga):
        ruta = DESCARGAS / f"{datetime.now():%Y%m%d-%H%M%S}-{descarga.suggested_filename}"
        descarga.save_as(ruta)
        registrar({"evento": "descarga", "archivo": descarga.suggested_filename})
        ok = subir(ruta)
        subidas.append(ok)
        if ok and not guardar:
            ruta.unlink(missing_ok=True)

    def preparar(pagina):
        pagina.on("download", al_descargar)
        pagina.on("framenavigated", lambda f: f == pagina.main_frame and registrar({"evento": "pagina", "url": f.url.split("?")[0]}))

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(PERFIL), channel="chrome", headless=False, no_viewport=True, accept_downloads=True)
        ctx.expose_binding("lincoyanClic", lambda _src, datos: registrar({"evento": "clic", **(datos or {})}))
        ctx.add_init_script(CLICS_JS)
        ctx.on("page", preparar)
        for pagina in ctx.pages:
            preparar(pagina)
        pagina = ctx.pages[0] if ctx.pages else ctx.new_page()
        pagina.goto(INICIO)
        print("Ingresa a BICE y descarga las cartolas de la tarjeta de crédito y de la cuenta.")
        print("Cada una se sube sola. Cierra la ventana cuando termines.")
        ctx.wait_for_event("close", timeout=0)

    registrar({"evento": "fin"})
    if not subidas:
        print("No se descargó ninguna cartola.")
    else:
        print(f"Listo: {sum(subidas)} de {len(subidas)} cartolas importadas.")


def main():
    ap = argparse.ArgumentParser(description="Sube las cartolas de BICE a Lincoyán.")
    ap.add_argument("--configurar", action="store_true", help="guarda el service token de Access")
    ap.add_argument("--archivo", help="sube este CSV sin abrir el navegador")
    ap.add_argument("--guardar", action="store_true", help="conserva los CSV descargados")
    args = ap.parse_args()
    if args.configurar:
        configurar()
    elif args.archivo:
        sys.exit(0 if subir(args.archivo) else 1)
    else:
        navegar(args.guardar)


if __name__ == "__main__":
    main()
