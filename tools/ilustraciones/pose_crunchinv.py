"""Crunch inverso en estilo silueta."""
from silueta_lib import *
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def abs_overlay(F, S, H, hoff, cls="m"):
    t, head, u, fr, hc = torso_shapes(S, H, hoff)
    L = (S - H).len()
    ov = [
        ell(H + u * (L * 0.42) + fr * 9.5, L * 0.36, 6.2, u.ang(), cls),
        ell(H + u * (L * 0.5) + fr * 3.5, L * 0.22, 3.4, u.ang(), cls),
    ]
    lines = []
    for k in (0.3, 0.46, 0.62):
        a = H + u * (L * k) + fr * 13
        b = H + u * (L * k) + fr * 6
        lines.append(f'<path class="dl" d="M{f(a.x)} {f(a.y)}L{f(b.x)} {f(b.y)}"/>')
    return F.clip(t[:1], ov + lines)


def draw():
    F = Fig("crunchinv")
    hoff = -1.0
    S, H = V(84, 133), V(122, 123.5)
    W = V(124, 140.5)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.y > b.y else b)
    th = math.radians(-106)
    K = H + V(math.cos(th), math.sin(th)) * L_TH
    sa = math.radians(12)
    A = K + V(math.cos(sa), math.sin(sa)) * L_SH
    d = (A - K).n()
    n = d.perp()
    heel = A + d * 2.5 + n * 2.5
    toe = A + d * 12 + n * -6
    Sf, Wf = S + V(-2, -1), W + V(-3, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.y > b.y else b)
    Hf = H + V(-2, -1)
    thf = math.radians(-102)
    Kf = Hf + V(math.cos(thf), math.sin(thf)) * L_TH
    saf = math.radians(16)
    Af = Kf + V(math.cos(saf), math.sin(saf)) * L_SH
    df = (Af - Kf).n()
    nf = df.perp()
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=heel, toe=toe,
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af,
             heelf=Af + df * 2.5 + nf * 2.5, toef=Af + df * 12 + nf * -6)
    back = [rrect(36, FLOOR - 4, 140, 4, 2, "pad")]
    fa, nr = person(F, J, set(), hoff=hoff)
    i = nr.index("</g>") + 4
    nr = nr[:i] + abs_overlay(F, S, H, hoff) + nr[i:]
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Crunch inverso">'
            f'<defs>{"".join(F.defs)}</defs>{floor()}{"".join(back)}{fa}{nr}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Crunch inverso</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}'
            f'<figcaption>Crunch inverso</figcaption></figure></body></html>')
    open(os.path.join(HERE, "pose_crunchinv.html"), "w", encoding="utf-8").write(html)
