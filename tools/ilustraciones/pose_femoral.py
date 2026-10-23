"""Curl femoral acostado: boca abajo en la máquina, rodillas flexionadas subiendo el rodillo."""
import math
import os

from silueta_lib import *

HERE = os.path.dirname(os.path.abspath(__file__))


def draw():
    F = Fig("femoral")
    hoff = -2.0
    H, S = V(92, 98), V(130, 101)
    K = V(61, 100)
    ang = math.radians(-75)
    A = K + V(math.cos(ang), math.sin(ang)) * L_SH
    Hf, Kf = V(90, 97), V(59, 99)
    angf = math.radians(-82)
    Af = Kf + V(math.cos(angf), math.sin(angf)) * L_SH

    def foot(K, A):
        d = (A - K).n()
        an = d.perp() * -1
        return A + d * 3.2 - an * 1.5, A + an * 12 + d * 5.5

    heel, toe = foot(K, A)
    heelf, toef = foot(Kf, Af)
    # manos en los mangos bajo la parte delantera del banco
    W = V(150, 121)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.y > b.y else b)
    Sf, Wf = S + V(-2, -1), W + V(-3, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.y > b.y else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=heel, toe=toe,
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=heelf, toef=toef)
    d = (A - K).n()
    an = d.perp() * -1
    roller = lerp(K, A, 0.86) - an * 8.4
    piv = K + V(-6, 10)
    grip = W + (W - E).n() * 3.4
    back = [
        # banco
        poly([V(50, 107), V(150, 113), V(150, 120), V(50, 114)], "pad", ' stroke-linejoin="round" stroke-width="5"'),
        line(V(60, 116), V(60, FLOOR - 2), "mkl", 5),
        line(V(140, 121), V(140, FLOOR - 2), "mkl", 5),
        rrect(40, FLOOR - 4, 124, 4, 2, "mk"),
        # mango
        line(grip, V(142, 121), "mkl", 3.5),
        # pila de pesas
        rrect(16, 40, 12, FLOOR - 40, 3, "mk"),
        rrect(28, 96, 14, 46, 2, "sk"),
        *[line(V(29, 100 + i * 6), V(41, 100 + i * 6), "sep", 1) for i in range(7)],
        rrect(12, FLOOR - 4, 40, 4, 2, "mk"),
        line(piv, V(28, 116), "mkl", 4),
    ]
    front = [line(piv, roller, "mkl", 3.4), circ(roller, 5.8, "pad"), circ(roller, 2, "mk"),
             circ(piv, 4, "pl"), circ(piv, 1.6, "mk")]
    fa, nr = person(F, J, {"hams"}, hoff=hoff, front_extra="".join(front))
    body = floor() + "".join(back) + fa + nr
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Curl femoral">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Curl femoral</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}</figure></body></html>')
    open(os.path.join(HERE, "pose_femoral.html"), "w", encoding="utf-8").write(html)
