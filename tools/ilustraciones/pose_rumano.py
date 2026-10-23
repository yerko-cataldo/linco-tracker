"""Peso muerto rumano: cadera atrás, barra a la altura de las rodillas."""
import math

from silueta_lib import *


def draw():
    F = Fig("rumano")
    A = V(97, 138.5)
    H = V(70, 82)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    lean = math.radians(58)
    u = V(math.sin(lean), -math.cos(lean))
    S = H + u * 39
    W = V(S.x + 1.5, S.y + 39)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    Af = A + V(-5, 0)
    Hf = H + V(-2, -1)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    Sf = S + V(-2, -1)
    Wf = W + V(-2, 0)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=A + V(-3, 4.1), toe=A + V(16, 5.1),
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=Af + V(-3, 4.1), toef=Af + V(16, 5.1))
    bar = W + (W - E).n() * 3.4
    back = [circ(bar, 19, "pl"), circ(bar, 13.5, "pl2"), circ(bar, 4.2, "mk")]
    fa, nr = person(F, J, {"hams", "glutes"}, front_extra=circ(bar, 2.3, "bar"))
    body = floor() + "".join(back) + fa + nr
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Peso muerto rumano">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')
