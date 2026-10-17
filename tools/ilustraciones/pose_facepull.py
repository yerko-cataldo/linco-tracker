from silueta_lib import *

OUT_HTML = __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "pose_facepull.html")


def draw():
    F = Fig("facepull")
    H, S = V(98, 79), V(93, 41)
    E = S + V(-12, -8)
    W = V(102, 27)
    A = V(102, 139)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    Sf = S + V(-2, -1)
    Ef = Sf + V(-11, -9)
    Wf = W + V(-2, -1)
    Hf, Af = H + V(-2, -1), V(88, 139)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=V(99, 142.6), toe=V(118, 143.6),
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=V(85, 142.6), toef=V(104, 143.6))
    grip = W + (W - E).n() * 3.4
    gripf = Wf + (Wf - Ef).n() * 3.4
    pul = V(156, 24)
    back = [
        rrect(160, 10, 12, FLOOR - 10, 3, "mk"),
        rrect(146, 96, 14, 46, 2, "sk"),
        *[line(V(147, 100 + i * 6), V(159, 100 + i * 6), "sep", 1) for i in range(7)],
        rrect(142, FLOOR - 4, 38, 4, 2, "mk"),
        rrect(152, 19, 10, 10, 2, "mk"),
        circ(pul, 5.5, "pl"), circ(pul, 1.8, "mk"),
        line(V(pul.x - 1, pul.y + 5.2), gripf, "cab", 1.1),
    ]
    t, _, u, fr, _ = torso_shapes(S, H)
    upper_back = F.clip(t, [ell(lerp(S, H, 0.14) - fr * 8, 5.5, 7.5, fr.ang(), "m")])
    upper = arm_shapes(S, E, W)[0][:1]
    rdelt = F.clip(upper, [ell(S + V(-4, -1), 7.5, 6.5, (E - S).ang(), "m")])
    rope = [line(V(pul.x - 1, pul.y + 5.2), grip, "cab", 1.1),
            line(grip + V(-1, 2), grip + V(0.5, 6.5), "barl", 2.2)]
    fa, nr = person(F, J, {"delt_rear"}, mid_extra=upper_back, front_extra=rdelt + circ(grip, 2.1, "bar"))
    body = floor() + "".join(back) + fa + "".join(rope) + nr
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Face pull">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Face pull</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}</figure></body></html>')
    open(OUT_HTML, "w", encoding="utf-8").write(html)
