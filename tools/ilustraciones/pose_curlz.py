from silueta_lib import *

HERE = __import__("os").path.dirname(__import__("os").path.abspath(__file__))


def zbar(a, b, w):
    """Barra Z entre dos puños, con dos quiebres."""
    d = b - a
    n = d.n().perp()
    pts = [a, lerp(a, b, 0.22) + n * 2.6, lerp(a, b, 0.4) - n * 2.0, lerp(a, b, 0.6) - n * 2.0,
           lerp(a, b, 0.78) + n * 2.6, b]
    s = " ".join(f"{f(p.x)},{f(p.y)}" for p in pts)
    return (f'<polyline class="barl" points="{s}" fill="none" stroke-width="{f(w)}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def plate(c, r):
    return circ(c, r, "pl") + circ(c, r * 0.66, "pl2") + circ(c, 2.4, "mk")


def draw():
    F = Fig("curlz")
    dx = -8
    A, Af = V(98 + dx, 139), V(93 + dx, 139)
    H, Hf = V(95 + dx, 77), V(92 + dx, 76)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    dv = V(0.78, 0.62)
    S = V(94 + dx, 38)
    Sf = S + V(-2, -1)
    E = S + V(2, 22.9)
    ang = math.radians(-22)
    fa = V(math.cos(ang), math.sin(ang)) * L_FA
    W = E + fa
    Wf = W + V(-2, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.y > b.y else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=V(95 + dx, 142.6), toe=V(114 + dx, 143.6),
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=V(89 + dx, 142.6), toef=V(108 + dx, 143.6))
    grip = W + (W - E).n() * 3.4
    gripf = Wf + (Wf - Ef).n() * 3.4
    back = [plate(grip, 14)]
    upper = arm_shapes(S, E, W)[0][:1]
    bic = F.clip(upper, [ell(lerp(S, E, 0.6) + ant(S, E) * 3.6, L_UA * 0.4, 5.0, (E - S).ang(), "m")])
    front = [bic, circ(grip, 2.4, "bar")]
    fa_, nr = person(F, J, {"biceps"}, front_extra="".join(front))
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Curl con barra Z">'
            f'<defs>{"".join(F.defs)}</defs>{floor()}{"".join(back)}{fa_}{nr}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Curl Z</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}</figure></body></html>')
    open(HERE + r"\pose_curlz.html", "w", encoding="utf-8").write(html)
