import os
from silueta_lib import *

HERE = os.path.dirname(os.path.abspath(__file__))
MAT = FLOOR - 4


def abs_overlay(F, S, H, cls="m"):
    t, head, u, fr, hc = torso_shapes(S, H, 2.0)
    T = (S - H).len() / 39
    c = H + u * (17 * T) + fr * 8.5
    ov = [ell(c, 14.5 * T, 6.2, u.ang(), cls)]
    lines = []
    for k in (11, 17, 23):
        a = H + u * (k * T) + fr * 4.2
        b = H + u * (k * T) + fr * 11.5
        lines.append(f'<path class="dl" d="M{f(a.x)} {f(a.y)}L{f(b.x)} {f(b.y)}"/>')
    a = H + u * (5 * T) + fr * 8.6
    b = H + u * (28 * T) + fr * 9.6
    lines.append(f'<path class="dl" d="M{f(a.x)} {f(a.y)}L{f(b.x)} {f(b.y)}"/>')
    return F.clip(t, ov + lines)


def hand_on(S, P):
    W = P
    for _ in range(6):
        E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.y < b.y else b)
        W = P - (W - E).n() * 3.4
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.y < b.y else b)
    return W, E


def draw():
    F = Fig("crunch")
    H = V(102, 130.5)
    u = V(-0.94, -0.342).n()
    fr = V(-u.y, u.x)
    S = H + u * 39
    hc = S + u * 20 + fr * 2.0
    W, E = hand_on(S, hc - fr * 3.0 - u * 1.0)
    heel = V(147, MAT - 3.2)
    toe = V(166, MAT - 2.2)
    A = heel + V(3, -3.6)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.y < b.y else b)
    Hf = H + V(-2, -1)
    Sf = S + V(-2, -1)
    Wf, Ef = hand_on(Sf, hc - fr * 3.0 - u * 1.0 + V(-2, -1))
    heelf = V(140, MAT - 3.2)
    toef = V(159, MAT - 2.2)
    Af = heelf + V(3, -3.6)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.y < b.y else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=heel, toe=toe,
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=heelf, toef=toef)
    back = [rrect(30, MAT, 140, FLOOR - MAT, 2, "pad")]
    fa, nr = person(F, J, set())
    i = nr.find("</g>") + 4
    nr = nr[:i] + abs_overlay(F, S, H) + nr[i:]
    body = floor() + "".join(back) + fa + nr
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Crunch">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Crunch</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}</figure></body></html>')
    open(os.path.join(HERE, "pose_crunch.html"), "w", encoding="utf-8").write(html)
