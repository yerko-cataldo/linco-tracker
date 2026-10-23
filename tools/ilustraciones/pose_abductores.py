"""Abductores en máquina: vista frontal, sentado, almohadillas por fuera de las rodillas."""
import os

from silueta_lib import CSS, Fig
from pose_aductores import front_seated

HERE = os.path.dirname(os.path.abspath(__file__))


def draw():
    return front_seated(Fig("abductores"), 36, False, {"abductors"}, "Abductores en máquina")


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Abductores en máquina</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}</figure></body></html>')
    open(os.path.join(HERE, "pose_abductores.html"), "w", encoding="utf-8").write(html)
