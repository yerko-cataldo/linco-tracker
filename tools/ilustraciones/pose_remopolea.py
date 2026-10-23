"""Remo sentado en polea baja: torso erguido, agarre al abdomen."""
from silueta_lib import *


def draw():
    F = Fig("remopolea")
    H = V(66, 110)
    S = V(68, 71)
    u = (S - H).n()
    fr = V(-u.y, u.x)
    W = V(81, 92)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    A = V(124, 117)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.y < b.y else b)
    heel, toe = V(129, 124), V(131, 105)
    Hf, Af = H + V(-2, -1), A + V(-3, -1)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.y < b.y else b)
    Sf = S + V(-2, -1)
    Wf = W + V(-2, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=heel, toe=toe,
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=heel + V(-3, -1), toef=toe + V(-3, -1))
    grip = W + (W - E).n() * 3.4
    pul = V(149, 97)
    back = [
        # columna y pila de pesas
        rrect(170, 14, 12, FLOOR - 14, 3, "mk"),
        rrect(156, 70, 14, 46, 2, "sk"),
        *[line(V(157, 74 + i * 6), V(169, 74 + i * 6), "sep", 1) for i in range(7)],
        rrect(146, FLOOR - 4, 40, 4, 2, "mk"),
        rrect(152, 64, 18, 4, 2, "mk"),
        # banco largo y base
        rrect(24, 118, 120, 7, 3.5, "pad"),
        rrect(40, 125, 6, FLOOR - 125, 2, "mk"),
        rrect(120, 125, 6, FLOOR - 125, 2, "mk"),
        rrect(20, FLOOR - 4, 130, 4, 2, "mk"),
        # plataforma de los pies
        poly([V(133, 100), V(139, 100), V(141, 128), V(135, 128)], "pad", ' stroke-linejoin="round" stroke-width="3"'),
        # polea baja y cable
        circ(pul, 4.5, "pl"), circ(pul, 1.6, "mk"),
        line(V(pul.x + 4.5, pul.y), V(pul.x + 4.5, 66), "cab", 1.1),
    ]
    cable = line(grip, V(pul.x, pul.y - 4.5), "cab", 1.1)
    handle = line(grip + V(-1, -6), grip + V(1, 6), "barl", 2.6)
    t = torso_shapes(S, H)[0]
    midback = F.clip(t, [ell(lerp(S, H, 0.22) - fr * 8, 5.5, 8, fr.ang(), "m")])
    fa, nr = person(F, J, {"lats", "biceps", "delt_rear"}, mid_extra=midback, front_extra=circ(grip, 2.2, "bar"))
    body = floor() + "".join(back) + fa + cable + handle + nr
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Remo en polea">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')
