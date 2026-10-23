"""Elevación de piernas en estilo silueta."""
from silueta_lib import *
from pose_crunchinv import abs_overlay
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MAT = FLOOR - 4


def leg_up(H, deg, lean=0.0):
    """Pierna extendida desde la cadera con ángulo deg sobre el suelo, pie en punta."""
    a = math.radians(-deg)
    d = V(math.cos(a), math.sin(a))
    K = H + d * L_TH
    A = K + d * L_SH
    an = d.perp() * -1
    heel = A - an * 2.6 + d * 1.5
    toe = A + d * 13 + an * 3.5
    return K, A, heel, toe


def draw():
    F = Fig("elevp")
    hoff = -2.0
    S, H = V(72, 131), V(111, 130.5)
    W = V(114, 139.5)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.y > b.y else b)
    K, A, heel, toe = leg_up(H, 62)
    Hf = H + V(-2, -1)
    Kf, Af, heelf, toef = leg_up(Hf, 64)
    Sf, Wf = S + V(-2, -1), W + V(-3, -0.5)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.y > b.y else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=heel, toe=toe,
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=heelf, toef=toef)
    back = [rrect(30, MAT, 140, FLOOR - MAT, 2, "pad")]
    fa, nr = person(F, J, set(), hoff=hoff)
    i = nr.index("</g>") + 4
    nr = nr[:i] + abs_overlay(F, S, H, hoff) + nr[i:]
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Elevación de piernas">'
            f'<defs>{"".join(F.defs)}</defs>{floor()}{"".join(back)}{fa}{nr}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Elevación de piernas</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}'
            f'<figcaption>Elevación de piernas</figcaption></figure></body></html>')
    open(os.path.join(HERE, "pose_elevpiernas.html"), "w", encoding="utf-8").write(html)
