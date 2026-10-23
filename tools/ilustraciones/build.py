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
import pose_pressinc, pose_militar, pose_laterales, pose_triceps  # noqa: E402,E401
import pose_femsentado, pose_femoral, pose_talones, pose_aductores, pose_abductores  # noqa: E402,E401
import pose_sentadilla, pose_remopolea, pose_rumano, pose_jalonmaq  # noqa: E402,E401
import pose_elevpiernas, pose_rueda, pose_plancha, pose_planchalat, pose_bicho  # noqa: E402,E401

INDEX = HERE.parent.parent / "public" / "index.html"
EXERCISES = {
    # Push
    "Press banca": lib.bench,
    "Press inclinado con mancuernas": pose_pressinc.draw,
    "Press militar": pose_militar.draw,
    "Elevaciones laterales": pose_laterales.draw,
    "Extensión de tríceps": pose_triceps.draw,
    # Pull
    "Jalón al pecho con polea": lib.pulldown,
    "Jalón al pecho en máquina": pose_jalonmaq.draw,
    "Remo en máquina": pose_remo.draw,
    "Remo en polea": pose_remopolea.draw,
    "Face pull": pose_facepull.draw,
    "Curl con barra Z": pose_curlz.draw,
    "Curl martillo": pose_martillo.draw,
    # Legs
    "Sentadilla": pose_sentadilla.draw,
    "Sentadilla hack": lib.hack,
    "Extensión de cuádriceps": lib.legext,
    "Peso muerto rumano": pose_rumano.draw,
    "Curl femoral": pose_femoral.draw,
    "Curl femoral sentado": pose_femsentado.draw,
    "Elevación de talones": pose_talones.draw,
    "Aductores en máquina": pose_aductores.draw,
    "Abductores en máquina": pose_abductores.draw,
    # Core
    "Crunch": pose_crunch.draw,
    "Crunch inverso": pose_crunchinv.draw,
    "Elevación de piernas": pose_elevpiernas.draw,
    "Rueda abdominal": pose_rueda.draw,
    "Plancha": pose_plancha.draw,
    "Plancha lateral": pose_planchalat.draw,
    "Bicho muerto": pose_bicho.draw,
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
