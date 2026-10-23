"""Press inclinado con mancuernas: banco a ~38°, mancuernas sobre el pecho alto."""
import math
import os

from silueta_lib import *
from pose_martillo import dumbbell

OUT_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pose_pressinc.html")


def draw():
    F = Fig("pressinc")
    ang = math.radians(38)
    u = V(-math.cos(ang), -math.sin(ang))
    fr = V(-u.y, u.x)
    bk = fr * -1
    H = V(104, 106)
    S = H + u * 39
    hoff = -1.0
    # brazos casi verticales sobre el pecho alto
    W = S + V(6, -39)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    A = V(136, 139)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.y < b.y else b)
    Sf, Wf = S + V(-2, -1), W + V(-2, -1.5)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    Hf, Af = H + V(-2, -1), V(127, 139)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.y < b.y else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=A + V(-3, 3.6), toe=A + V(16, 4.6),
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=Af + V(-3, 3.6), toef=Af + V(16, 4.6))
    grip = W + (W - E).n() * 3.4
    # respaldo inclinado
    pa = H + bk * 10.5 + u * 2
    pb = H + bk * 10.5 + u * 62
    rest = [pa, pb, pb + bk * 7, pa + bk * 7]
    mid_rest = lerp(pa, pb, 0.45) + bk * 7
    back = [
        # base y patas
        rrect(46, FLOOR - 4, 88, 4, 2, "mk"),
        rrect(100, 120, 6, FLOOR - 120, 2, "mk"),
        line(mid_rest, V(mid_rest.x + 6, FLOOR - 3), "mkl", 4),
        # asiento
        rrect(80, 110, 40, 8, 4, "pad"),
        poly(rest, "pad", ' stroke-linejoin="round" stroke-width="5"'),
    ]
    fa, nr = person(F, J, {"chest", "delt_front", "triceps"}, hoff=hoff, mid_extra=dumbbell(grip, V(1, 0)))
    body = floor() + "".join(back) + fa + nr
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Press inclinado con mancuernas">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Press inclinado</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}</figure></body></html>')
    open(OUT_HTML, "w", encoding="utf-8").write(html)
