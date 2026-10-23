"""Extensión de tríceps en polea alta con cuerda, de pie."""
import os

from silueta_lib import *

OUT_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pose_triceps.html")


def draw():
    F = Fig("triceps")
    H, S = V(94, 79), V(100, 41)
    A = V(97, 138.5)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    Hf, Af = V(92, 78), V(85, 138.5)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    # codo pegado al costado, antebrazo extendido hacia abajo
    E = S + V(-1.5, 22.9)
    W = E + V(6, 17.9)
    Sf = S + V(-2, -1)
    Ef = Sf + V(-1.5, 22.9)
    Wf = Ef + V(6, 17.9)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=A + V(-3, 4.1), toe=A + V(16, 5.1),
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=Af + V(-3, 4.1), toef=Af + V(16, 5.1))
    grip = W + (W - E).n() * 3.4
    gripf = Wf + (Wf - Ef).n() * 3.4
    pul = V(152, 16)
    top = V(pul.x - 4.5, pul.y + 3)
    knot = V(grip.x + 3, grip.y - 10)
    back = [
        rrect(156, 8, 12, FLOOR - 8, 3, "mk"),
        rrect(142, 96, 14, 46, 2, "sk"),
        *[line(V(143, 100 + i * 6), V(155, 100 + i * 6), "sep", 1) for i in range(7)],
        rrect(138, FLOOR - 4, 38, 4, 2, "mk"),
        rrect(146, 11, 12, 10, 2, "mk"),
        circ(pul, 5.5, "pl"), circ(pul, 1.8, "mk"),
        line(top, knot, "cab", 1.1),
        line(knot, gripf, "barl", 2.2),
    ]
    rope = [line(knot, grip, "barl", 2.2), circ(knot, 1.8, "bar")]
    fa, nr = person(F, J, {"triceps"})
    body = floor() + "".join(back) + fa + "".join(rope) + nr + circ(grip + V(0, 3.5), 2.0, "bar")
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Extensión de tríceps">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Extensión de tríceps</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}</figure></body></html>')
    open(OUT_HTML, "w", encoding="utf-8").write(html)
