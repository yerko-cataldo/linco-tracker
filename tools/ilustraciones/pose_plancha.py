"""Plancha sobre antebrazos en estilo silueta."""
from silueta_lib import *
from pose_crunchinv import abs_overlay
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MAT = FLOOR - 4


def foot_tucked(toe, deg=72):
    """Pie apoyado en la punta: talón arriba, planta hacia atrás."""
    a = math.radians(deg)
    fd = V(math.cos(a), math.sin(a))  # del talón a la punta
    heel = toe - fd * 19
    A = heel + fd * 3 - fd.perp() * 3.6
    return A, heel, toe


def draw():
    F = Fig("plancha")
    hoff = 1.0
    E = V(146, MAT - 4.2)
    S = E + V(0, -L_UA)
    W = E + V(L_FA, 0.4)
    toe = V(38, MAT - 1.8)
    A, heel, toe = foot_tucked(toe)
    d = (A - S).n()
    L = (A - S).len()
    k = L / (39 + L_TH + L_SH)
    H = S + d * (39 * k)
    K = H + d * (L_TH * k)
    Ef, Sf = E + V(-2, -1), S + V(-2, -1)
    Wf = W + V(-2, -1)
    Hf, Kf = H + V(-2, -1), K + V(-2, -1)
    Af, heelf, toef = foot_tucked(toe + V(-2.5, 0))
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=heel, toe=toe,
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=heelf, toef=toef)
    back = [rrect(22, MAT, 156, FLOOR - MAT, 2, "pad")]
    fa, nr = person(F, J, set(), hoff=hoff)
    i = nr.index("</g>") + 4
    nr = nr[:i] + abs_overlay(F, S, H, hoff) + nr[i:]
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Plancha">'
            f'<defs>{"".join(F.defs)}</defs>{floor()}{"".join(back)}{fa}{nr}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Plancha</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}'
            f'<figcaption>Plancha</figcaption></figure></body></html>')
    open(os.path.join(HERE, "pose_plancha.html"), "w", encoding="utf-8").write(html)
