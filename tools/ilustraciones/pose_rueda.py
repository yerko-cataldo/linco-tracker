"""Rueda abdominal en estilo silueta."""
from silueta_lib import *
from pose_crunchinv import abs_overlay
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MAT = FLOOR - 4


def foot_flat(A):
    """Empeine apoyado en la colchoneta, dedos hacia atrás (izquierda)."""
    heel = A + V(2.5, -3.2)
    toe = V(A.x - 15, MAT - 1.8)
    return heel, toe


def draw():
    F = Fig("rueda")
    hoff = 1.0
    ang = math.radians(-25)
    d = V(math.cos(ang), math.sin(ang))
    K = V(72, MAT - 5.2)
    H = K + d * L_TH
    S = H + d * 39
    R = 12.5
    wc = V(174, MAT - R)
    W = wc + V(-2.6, -1.2)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.y < b.y else b)
    A = K + V(-L_SH, 0.6)
    heel, toe = foot_flat(A)
    Kf, Hf, Sf = K + V(-2, -1), H + V(-2, -1), S + V(-2, -1.2)
    Af = A + V(-2, -1)
    heelf, toef = foot_flat(Af)
    Wf = W + V(-1, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.y < b.y else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=heel, toe=toe,
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=heelf, toef=toef)
    back = [rrect(18, MAT, 124, FLOOR - MAT, 2, "pad"),
            circ(wc + V(-1.5, -0.8), R, "pl")]
    wheel = [circ(wc, R, "pl"), circ(wc, R - 4, "pl2"), line(wc + V(-4.5, -1.5), wc + V(4.5, 1.5), "barl", 2.6),
             circ(wc, 2.6, "bar")]
    fa, nr = person(F, J, set(), hoff=hoff, mid_extra="".join(wheel))
    i = nr.index("</g>") + 4
    nr = nr[:i] + abs_overlay(F, S, H, hoff) + nr[i:]
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Rueda abdominal">'
            f'<defs>{"".join(F.defs)}</defs>{floor()}{"".join(back)}{fa}{nr}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Rueda abdominal</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}'
            f'<figcaption>Rueda abdominal</figcaption></figure></body></html>')
    open(os.path.join(HERE, "pose_rueda.html"), "w", encoding="utf-8").write(html)
