"""Inserta las ilustraciones de ejercicios en public/index.html.

Genera el SVG de cada ejercicio con silueta_lib.py y los módulos pose_*.py, y reemplaza
el objeto ILLU entre los marcadores /* ILLU:inicio */ y /* ILLU:fin */.

Uso: py tools/ilustraciones/build.py
"""
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import silueta_lib as lib  # noqa: E402
import pose_crunch, pose_crunchinv, pose_curlz, pose_facepull, pose_martillo, pose_remo  # noqa: E402,E401

INDEX = HERE.parent.parent / "public" / "index.html"
EXERCISES = {
    "Jalón al pecho con polea": lib.pulldown,
    "Remo en máquina": pose_remo.draw,
    "Face pull": pose_facepull.draw,
    "Curl con barra Z": pose_curlz.draw,
    "Curl martillo": pose_martillo.draw,
    "Crunch": pose_crunch.draw,
    "Crunch inverso": pose_crunchinv.draw,
}


def clean(svg: str) -> str:
    svg = re.search(r"<svg.*?</svg>", svg, re.S).group(0)
    svg = re.sub(r'\s(role|aria-label)="[^"]*"', "", svg)
    return svg.replace("<svg ", '<svg aria-hidden="true" ', 1)


def main() -> None:
    items = ",\n".join(f"  {json.dumps(name, ensure_ascii=False)}: {json.dumps(clean(fn()), ensure_ascii=False)}" for name, fn in EXERCISES.items())
    block = f"/* ILLU:inicio */\nconst ILLU = {{\n{items}\n}};\n/* ILLU:fin */"
    html = INDEX.read_text(encoding="utf-8")
    new, n = re.subn(r"/\* ILLU:inicio \*/.*?/\* ILLU:fin \*/", lambda _: block, html, flags=re.S)
    if n != 1:
        raise SystemExit("No encontré los marcadores ILLU en public/index.html")
    INDEX.write_text(new, encoding="utf-8", newline="\n")
    print(f"{len(EXERCISES)} ilustraciones, {len(block) // 1024} KB")


if __name__ == "__main__":
    main()
