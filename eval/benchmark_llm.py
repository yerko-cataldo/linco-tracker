"""
Benchmark de modelos para el coach de Lincoyán.

Compara modelos gratis de Cloudflare Workers AI contra Claude Haiku en las dos
tareas que más usa la app:
  1. Estimar kcal y macros de una comida descrita en texto (20 casos con
     referencia tipo USDA FoodData Central, porciones en gramos explícitas).
  2. Convertir un relato del día en registros estructurados (8 casos con
     respuesta esperada campo por campo).

Métricas: tasa de JSON válido, MAE y MAPE de kcal, MAE de proteína,
sesgo (error medio con signo), exactitud por campo y latencia mediana.

Uso:
    pip install requests pandas
    export CF_ACCOUNT_ID=...          # Overview de tu dominio, panel derecho "Account ID"
    export CF_API_TOKEN=...           # token con permiso Workers AI (ver README)
    export ANTHROPIC_API_KEY=...      # opcional: sin esto solo prueba Workers AI
    python eval/benchmark_llm.py

Salidas (en eval/results/): raw.csv con cada respuesta y summary.csv.
"""
from __future__ import annotations

import json
import os
import re
import statistics
import sys
import time
from pathlib import Path

import pandas as pd
import requests

# --------------------------------------------------------------------------
# Modelos a evaluar. Los que no existan en tu cuenta se omiten con aviso;
# al inicio se imprime la lista de modelos de texto disponibles.
# --------------------------------------------------------------------------
CF_MODELS = [
    "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
    "@cf/meta/llama-4-scout-17b-16e-instruct",
    "@cf/meta/llama-3.2-11b-vision-instruct",
    "@cf/meta/llama-3.1-8b-instruct",
]
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
REPEATS = 1          # súbelo a 3 para medir la variabilidad de cada modelo
TIMEOUT = 90

# --------------------------------------------------------------------------
# Tarea 1: comidas con referencia (aprox. USDA FoodData Central, por porción)
# kcal, proteína g, carbohidratos g, grasa g
# --------------------------------------------------------------------------
MEALS = [
    ("200 g de pechuga de pollo cocida sin piel", 330, 62, 0, 7),
    ("2 huevos enteros grandes revueltos sin aceite", 144, 12.6, 0.8, 9.6),
    ("150 g de arroz blanco cocido", 195, 4, 42, 0.5),
    ("1 plátano mediano de 120 g", 107, 1.3, 27.5, 0.4),
    ("100 g de palta hass", 160, 2, 8.5, 14.7),
    ("40 g de avena en hojuelas (en seco)", 156, 6.8, 26.5, 2.8),
    ("1 cucharada de aceite de oliva (13 g)", 115, 0, 0, 13),
    ("30 g de almendras", 174, 6.4, 6.5, 15),
    ("200 g de fideos cocidos sin salsa", 316, 11.6, 62, 1.9),
    ("150 g de brócoli cocido", 52, 3.6, 10.8, 0.6),
    ("150 g de tomate", 27, 1.3, 5.8, 0.3),
    ("10 g de mantequilla", 72, 0.1, 0, 8.1),
    ("150 g de pechuga de pollo cocida con 150 g de arroz blanco cocido", 443, 50.5, 42, 5.9),
    ("2 huevos revueltos con 50 g de palta", 224, 13.6, 5, 17),
    ("40 g de avena con 1 plátano mediano (120 g)", 263, 8.1, 54, 3.2),
    ("200 g de fideos cocidos con 1 cucharada de aceite de oliva", 431, 11.6, 62, 14.9),
    ("ensalada de 150 g de tomate con 100 g de palta y 1 cucharada de aceite de oliva", 302, 3.3, 14.3, 28),
    ("150 g de pollo cocido, 150 g de brócoli cocido y 100 g de arroz cocido", 430, 53, 39, 6.3),
    ("3 huevos duros", 216, 18.9, 1.2, 14.4),
    ("30 g de almendras y 1 plátano mediano (120 g)", 281, 7.7, 34, 15.4),
]

MEAL_PROMPT = """Eres un nutricionista. Estima calorías y macronutrientes de esta comida.
Usa las cantidades indicadas; no asumas ingredientes que no se mencionan.
Comida: {meal}
Responde solo con un JSON, sin texto adicional:
{{"kcal": number, "p": number, "c": number, "f": number}}"""

# --------------------------------------------------------------------------
# Tarea 2: registro rápido con respuesta esperada (rutas tipo "act.walkMin")
# --------------------------------------------------------------------------
CATALOG = {
    "tecnicas": [{"id": "t1", "nombre": "Octavas"}, {"id": "t2", "nombre": "Slap"}],
    "libros_cursos": [{"id": "b1", "titulo": "Statistical Rethinking", "unidad": "páginas"}],
}
QUICK = [
    ("hoy hice pull 40 minutos y paseé al galgo 90 minutos",
     {"act.gym": "pull", "act.gymMin": 40, "act.walkMin": 90}),
    ("practiqué bajo 35 min, slap a 92 bpm limpio",
     {"bassMinutes": 35, "bassLogs.0.techId": "t2", "bassLogs.0.bpm": 92, "bassLogs.0.clean": True}),
    ("leí 25 páginas de Statistical Rethinking en 40 minutos",
     {"study.0.itemId": "b1", "study.0.amount": 25, "study.0.minutes": 40}),
    ("tenis 90 min y después 20 km en bici en una hora",
     {"act.tennisMin": 90, "act.bikeKm": 20, "act.bikeMin": 60}),
    ("octavas a 110 pero me equivoqué harto, 20 minutos de práctica",
     {"bassLogs.0.techId": "t1", "bassLogs.0.bpm": 110, "bassLogs.0.clean": False, "bassMinutes": 20}),
    ("me pesé 91.4 kg y llevo 6 vasos de agua",
     {"weight": 91.4, "water": 6}),
    ("día de piernas 45 min, y el paseo con el perro fue cortito, 30 min",
     {"act.gym": "legs", "act.gymMin": 45, "act.walkMin": 30}),
    ("una hora de bajo: slap a 100 limpio y octavas a 120 limpio",
     {"bassMinutes": 60, "bassLogs.0.bpm": 100, "bassLogs.1.bpm": 120}),
]

QUICK_PROMPT = """Convierte el relato de un día en registros para una bitácora personal.
Catálogo existente (usa estos id cuando el texto se refiera a ellos): {catalog}
"Paseo" o "caminata con el perro/galgo" va en act.walkMin. "Día de piernas" es gym "legs".
No inventes lo que el texto no menciona: usa null o listas vacías.
Texto: \"\"\"{text}\"\"\"
Responde solo con este JSON, sin texto adicional:
{{"act":{{"gym":"push"|"pull"|"legs"|"full"|null,"gymMin":number|null,"walkMin":number|null,"tennisMin":number|null,"bikeMin":number|null,"bikeKm":number|null}},
 "bassMinutes": number|null,
 "bassLogs":[{{"techId":string|null,"techName":string|null,"bpm":number,"clean":boolean}}],
 "study":[{{"itemId":string|null,"amount":number|null,"minutes":number|null}}],
 "weight": number|null, "water": number|null}}"""


# --------------------------------------------------------------------------
# Clientes
# --------------------------------------------------------------------------
def cf_list_models(account: str, token: str) -> list[str]:
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/models/search"
    r = requests.get(url, headers={"Authorization": f"Bearer {token}"},
                     params={"task": "Text Generation", "per_page": 100}, timeout=TIMEOUT)
    r.raise_for_status()
    return sorted(m["name"] for m in r.json().get("result", []))


def cf_run(model: str, prompt: str, account: str, token: str) -> str:
    url = f"https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"
    r = requests.post(url, headers={"Authorization": f"Bearer {token}"},
                      json={"messages": [{"role": "user", "content": prompt}], "max_tokens": 800},
                      timeout=TIMEOUT)
    r.raise_for_status()
    res = r.json().get("result", {})
    # Los modelos devuelven formatos distintos: {"response": "..."} o estilo OpenAI
    if isinstance(res.get("response"), (dict, list)):
        return json.dumps(res["response"])
    if "response" in res:
        return str(res["response"])
    if "choices" in res:
        return res["choices"][0]["message"]["content"]
    return json.dumps(res)


def anthropic_run(prompt: str, key: str) -> str:
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": ANTHROPIC_MODEL, "max_tokens": 800,
              "system": "Responde únicamente con JSON válido, sin texto adicional ni bloques de código.",
              "messages": [{"role": "user", "content": prompt}]},
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return "".join(b.get("text", "") for b in r.json().get("content", []))


# --------------------------------------------------------------------------
# Utilidades de evaluación
# --------------------------------------------------------------------------
def parse_json(text: str):
    t = re.sub(r"```(?:json)?", "", text or "").strip()
    a, b = t.find("{"), t.rfind("}")
    if a < 0 or b <= a:
        return None
    try:
        return json.loads(t[a:b + 1])
    except json.JSONDecodeError:
        return None


def get_path(obj, path: str):
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return None
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
    return cur


def same(got, exp) -> bool:
    if isinstance(exp, bool):
        return got is exp
    if isinstance(exp, (int, float)):
        try:
            return abs(float(got) - exp) <= max(0.5, abs(exp) * 0.02)
        except (TypeError, ValueError):
            return False
    return str(got).strip().lower() == str(exp).lower()


def to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# --------------------------------------------------------------------------
# Ejecución
# --------------------------------------------------------------------------
def main() -> int:
    account, token = os.environ.get("CF_ACCOUNT_ID"), os.environ.get("CF_API_TOKEN")
    akey = os.environ.get("ANTHROPIC_API_KEY")
    if not (account and token):
        print("Falta CF_ACCOUNT_ID o CF_API_TOKEN.", file=sys.stderr)
        return 1

    available = cf_list_models(account, token)
    print(f"Modelos de texto disponibles en Workers AI ({len(available)}):")
    for name in available:
        print("  ", name)
    models = [m for m in CF_MODELS if m in available]
    for m in CF_MODELS:
        if m not in available:
            print(f"Aviso: {m} no está disponible; se omite. Edita CF_MODELS con uno de la lista.")

    runners = {m: (lambda p, m=m: cf_run(m, p, account, token)) for m in models}
    if akey:
        runners[ANTHROPIC_MODEL] = lambda p: anthropic_run(p, akey)
    if not runners:
        print("No hay modelos para evaluar.", file=sys.stderr)
        return 1

    rows = []
    for name, run in runners.items():
        print(f"\n== {name}")
        for rep in range(REPEATS):
            for meal, kcal, p, c, f in MEALS:
                t0 = time.perf_counter()
                try:
                    out, err = run(MEAL_PROMPT.format(meal=meal)), ""
                except Exception as e:  # noqa: BLE001
                    out, err = "", str(e)[:200]
                dt = time.perf_counter() - t0
                js = parse_json(out)
                rows.append({"model": name, "task": "meal", "rep": rep, "case": meal, "latency_s": dt,
                             "json_ok": js is not None, "error": err, "raw": out[:2000],
                             "ref_kcal": kcal, "ref_p": p, "ref_c": c, "ref_f": f,
                             "kcal": to_float(get_path(js, "kcal")) if js else None,
                             "p": to_float(get_path(js, "p")) if js else None,
                             "c": to_float(get_path(js, "c")) if js else None,
                             "f": to_float(get_path(js, "f")) if js else None})
                print(".", end="", flush=True)
            for text, expected in QUICK:
                t0 = time.perf_counter()
                try:
                    out, err = run(QUICK_PROMPT.format(catalog=json.dumps(CATALOG, ensure_ascii=False), text=text)), ""
                except Exception as e:  # noqa: BLE001
                    out, err = "", str(e)[:200]
                dt = time.perf_counter() - t0
                js = parse_json(out)
                hits = [same(get_path(js, k), v) for k, v in expected.items()] if js else [False] * len(expected)
                rows.append({"model": name, "task": "quick", "rep": rep, "case": text, "latency_s": dt,
                             "json_ok": js is not None, "error": err, "raw": out[:2000],
                             "fields": len(hits), "fields_ok": sum(hits)})
                print(".", end="", flush=True)

    df = pd.DataFrame(rows)
    outdir = Path(__file__).parent / "results"
    outdir.mkdir(exist_ok=True)
    df.to_csv(outdir / "raw.csv", index=False)

    summary = []
    for name, g in df.groupby("model", sort=False):
        meal = g[g.task == "meal"]
        ok = meal.dropna(subset=["kcal"])
        quick = g[g.task == "quick"]
        err_k = ok.kcal - ok.ref_kcal
        summary.append({
            "modelo": name,
            "json_ok_%": round(100 * g.json_ok.mean(), 1),
            "kcal_MAE": round(err_k.abs().mean(), 1) if len(ok) else None,
            "kcal_MAPE_%": round(100 * (err_k.abs() / ok.ref_kcal).mean(), 1) if len(ok) else None,
            "kcal_sesgo": round(err_k.mean(), 1) if len(ok) else None,
            "prot_MAE_g": round((ok.p - ok.ref_p).abs().mean(), 1) if len(ok) else None,
            "registro_campos_ok_%": round(100 * quick.fields_ok.sum() / max(1, quick.fields.sum()), 1),
            "latencia_mediana_s": round(statistics.median(g.latency_s), 2),
            "errores_api": int((g.error != "").sum()),
        })
    s = pd.DataFrame(summary)
    s.to_csv(outdir / "summary.csv", index=False)
    print("\n\nResumen:\n")
    print(s.to_string(index=False))
    print(f"\nDetalle en {outdir / 'raw.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
