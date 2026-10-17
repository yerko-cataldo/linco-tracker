"""Curl martillo: figura de pie de perfil con mancuernas en agarre neutro."""
import math
import os

from silueta_lib import *

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_HTML = os.path.join(HERE, "pose_martillo.html")


def rot_rect(c, along, w_along, w_across):
    """Rectángulo rotado centrado en c, con lado w_along en la dirección along."""
    d = along.n()
    p = d.perp()
    a, b = d * (w_along / 2), p * (w_across / 2)
    return [c - a - b, c + a - b, c + a + b, c - a + b]


def dumbbell(c, along, cls_head="pad"):
    """Mancuerna centrada en c con el mango en la dirección along."""
    d = along.n()
    out = [line(c - d * 8, c + d * 8, "barl", 2.4)]
    for s in (-1, 1):
        hc = c + d * (s * 8.2)
        out.append(poly(rot_rect(hc, d, 4.6, 10.5), cls_head, ' stroke-linejoin="round" stroke-width="2.4"'))
        out.append(poly(rot_rect(hc + d * (s * 3.2), d, 1.8, 7), cls_head, ' stroke-linejoin="round" stroke-width="1.6"'))
    return "".join(out)


def forearm_ov(F, E, W, cls):
    """Antebrazo (braquiorradial y extensores) recortado a la silueta del antebrazo."""
    fa = [outline(E, W, FA_A, FA_P)]
    L = (W - E).len()
    return F.clip(fa, [ell(lerp(E, W, 0.32) + ant(E, W) * 1.6, L * 0.36, 4.4, (W - E).ang(), cls)])


def draw():
    F = Fig("martillo")
    # tronco y piernas
    H, S = V(94, 77), V(95, 38)
    A = V(95, 138.5)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    Hf, Af = V(92, 76), V(89, 138.5)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    # brazo cercano: codo pegado al costado, antebrazo subiendo
    E = S + V(1.5, 22.9)
    ang = math.radians(-28)
    W = E + V(math.cos(ang), math.sin(ang)) * L_FA
    # brazo lejano: colgando junto al muslo
    Sf = S + V(-2, -1)
    Ef = Sf + V(4, 22.6)
    Wf = Ef + V(9.5, 16.5)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=A + V(-3, 4.1), toe=A + V(16, 5.1),
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=Af + V(-3, 4.1), toef=Af + V(16, 5.1))
    grip = W + (W - E).n() * 3.4
    gripf = Wf + (Wf - Ef).n() * 3.4
    hi = {"biceps"}
    mid = dumbbell(grip, V(0, 1))
    front = forearm_ov(F, E, W, "m")
    fa, nr = person(F, J, hi, mid_extra=mid, front_extra=front)
    far_extra = forearm_ov(F, Ef, Wf, "mf")
    back = dumbbell(gripf, V(1, 0))
    # capas: mancuerna lejana, figura lejana, antebrazo lejano, figura cercana
    body = floor() + back + fa + far_extra + nr
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Curl martillo">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Curl martillo</title>'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><style>{CSS}</style></head>'
            f'<body><figure style="width:600px">{draw()}<figcaption>Curl martillo</figcaption></figure></body></html>')
    open(OUT_HTML, "w", encoding="utf-8").write(html)
