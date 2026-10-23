"""Curl femoral sentado: máquina con almohadilla sobre los muslos y rodillo tras los tobillos."""
import math
import os

from silueta_lib import *

HERE = os.path.dirname(os.path.abspath(__file__))


def draw():
    F = Fig("femsent")
    H, S = V(82, 104), V(75, 66)
    W = V(95, 103)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    K = V(114, 104)
    ang = math.radians(112)
    A = K + V(math.cos(ang), math.sin(ang)) * L_SH
    Kf = V(111, 103)
    angf = math.radians(106)
    Af = Kf + V(math.cos(angf), math.sin(angf)) * L_SH

    def foot(K, A):
        d = (A - K).n()
        an = d.perp() * -1
        return A + d * 3.2 - an * 1.5, A + an * 12 + d * 5.5

    heel, toe = foot(K, A)
    heelf, toef = foot(Kf, Af)
    Sf, Wf = V(73, 65), V(92, 102)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=heel, toe=toe,
             Sf=Sf, Hf=V(80, 103), Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=heelf, toef=toef)
    d = (A - K).n()
    an = d.perp() * -1
    roller = lerp(K, A, 0.84) - an * 8.4
    piv = K + V(1, 0)
    # almohadilla sobre los muslos, cerca de la rodilla
    tp = V(103, 92.5)
    grip = W + (W - E).n() * 3.4
    back = [
        # pila de pesas
        rrect(16, 26, 12, FLOOR - 26, 3, "mk"),
        rrect(28, 96, 14, 46, 2, "sk"),
        *[line(V(29, 100 + i * 6), V(41, 100 + i * 6), "sep", 1) for i in range(7)],
        rrect(12, FLOOR - 4, 40, 4, 2, "mk"),
        # respaldo
        poly([V(55, 50), V(62, 49), V(69, 109), V(62, 109)], "pad", ' stroke-linejoin="round" stroke-width="5"'),
        line(V(60, 112), V(28, 60), "mkl", 4),
        # asiento y estructura
        rrect(80, 121, 6, FLOOR - 121, 2, "mk"),
        rrect(60, FLOOR - 4, 52, 4, 2, "mk"),
        rrect(60, 112, 46, 9, 4.5, "pad"),
        # soporte de la almohadilla de muslos
        line(tp + V(8, 0), V(136, 74), "mkl", 4),
        line(V(136, 74), V(136, FLOOR - 2), "mkl", 5),
        rrect(122, FLOOR - 4, 30, 4, 2, "mk"),
        line(piv, V(136, 104), "mkl", 4),
        # mango junto al asiento
        line(grip, V(grip.x, 121), "mkl", 3.5),
    ]
    mid = rrect(tp.x - 13, tp.y - 4.5, 26, 9, 4.5, "pad")
    front = [
        line(piv, roller, "mkl", 3.4), circ(roller, 5.8, "pad"), circ(roller, 2, "mk"),
        circ(piv, 4, "pl"), circ(piv, 1.6, "mk"),
    ]
    fa, nr = person(F, J, {"hams"}, mid_extra=mid, front_extra="".join(front))
    body = floor() + "".join(back) + fa + nr
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Curl femoral sentado">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Curl femoral sentado</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}</figure></body></html>')
    open(os.path.join(HERE, "pose_femsentado.html"), "w", encoding="utf-8").write(html)
