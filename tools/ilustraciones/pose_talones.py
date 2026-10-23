"""Elevación de talones: de pie en la máquina, puntas sobre el escalón y talones arriba."""
import math
import os

from silueta_lib import *
from pose_martillo import dumbbell

HERE = os.path.dirname(os.path.abspath(__file__))
STEP = FLOOR - 5.5


def rot(p, c, deg):
    a = math.radians(deg)
    d = p - c
    return c + V(d.x * math.cos(a) - d.y * math.sin(a), d.x * math.sin(a) + d.y * math.cos(a))


def foot_on_toes(ball_x, deg):
    """Pie en punta: devuelve (tobillo, talón, punta) con la planta del antepié sobre el escalón."""
    A0 = V(0, 0)
    heel0, toe0 = A0 + V(-3, 4.1), A0 + V(16, 5.1)
    ball0 = lerp(heel0, toe0, 0.68)
    A, heel, toe = (rot(p, ball0, deg) for p in (A0, heel0, toe0))
    off = V(ball_x, STEP - 2.5) - ball0
    return A + off, heel + off, toe + off


def draw():
    F = Fig("talones")
    A, heel, toe = foot_on_toes(106, 27)
    Af, heelf, toef = foot_on_toes(100, 27)
    reach = L_TH + L_SH - 2.2
    H = A + V(-1.5, -reach)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    Hf = V(H.x - 2, H.y - 1)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    S = H + V(1, -39)
    u = (S - H).n()
    fr = V(-u.y, u.x)
    # brazos colgando con una mancuerna en cada mano
    W = S + V(4, 40.6)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    Sf = S + V(-2, -1)
    Wf = W + V(-3, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=heel, toe=toe,
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=heelf, toef=toef)
    grip = W + (W - E).n() * 3.4
    gripf = Wf + (Wf - Ef).n() * 3.4
    back = [
        # escalón
        rrect(97, STEP, 44, FLOOR - STEP + 1, 2, "pad"),
        dumbbell(gripf, V(1, 0)),
    ]
    th, sh, _ = leg_shapes(H, K, A, heel, toe)
    calf = leg_overlays(F, H, K, A, th, sh, {"calves"}, "m")
    # brazo cercano encima del muslo, para que la mano y la mancuerna se lean
    arm, hand = arm_shapes(S, E, W)
    arm_top = (dumbbell(grip, V(1, 0)) + f'<g class="halo">{"".join(arm + hand)}</g><g class="b">{"".join(arm + hand)}</g>'
               + F.clip(arm[:1], [ell(lerp(S, E, 0.1), 6.0, 7.0, (E - S).ang(), "t")]))
    fa, nr = person(F, J, {"calves"}, front_extra=calf + arm_top)
    body = floor() + "".join(back) + fa + nr
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Elevación de talones">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Elevación de talones</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}</figure></body></html>')
    open(os.path.join(HERE, "pose_talones.html"), "w", encoding="utf-8").write(html)
