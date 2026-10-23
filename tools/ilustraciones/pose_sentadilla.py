"""Sentadilla con barra en la espalda, en el punto bajo."""
import math

from silueta_lib import *


def draw():
    F = Fig("sentadilla")
    A = V(99, 138.5)
    K = V(114, 110)
    H = V(84, 105)
    lean = math.radians(50)
    u = V(math.sin(lean), -math.cos(lean))
    fr = V(-u.y, u.x)
    S = H + u * 39
    bar = S - fr * 8.5 + u * 1.5
    # codo atrás, bajo la barra; antebrazo sube hasta la barra
    E = S - u * 18 - fr * 12
    W = E + (bar - E).n() * (L_FA - 1.5)
    Af = A + V(-5, 0)
    Kf = K + V(-3, -1)
    Hf = H + V(-2, -1)
    Sf = S + V(-2, -1)
    Ef = E + V(-2, -1)
    Wf = W + V(-2, -1)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=A + V(-3, 4.1), toe=A + V(16, 5.1),
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=Af + V(-3, 4.1), toef=Af + V(16, 5.1))
    back = [circ(bar, 19, "pl"), circ(bar, 13.5, "pl2"), circ(bar, 4.2, "mk")]
    front = circ(bar, 2.4, "bar")
    fa, nr = person(F, J, {"quads", "glutes"}, front_extra=front)
    body = floor() + "".join(back) + fa + nr
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Sentadilla">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')
