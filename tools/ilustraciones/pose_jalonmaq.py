"""Jalón al pecho en máquina de palanca (con discos, sin cable)."""
from silueta_lib import *


def draw():
    F = Fig("jalonmaq")
    H, S = V(80, 104), V(73, 66)
    W = V(90, 60)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.y > b.y else b)
    A = V(110, 139)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    Sf, Wf = V(71, 65), V(87, 59)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.y > b.y else b)
    Hf, Af = V(78, 103), V(103, 139)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=V(107, 142.6), toe=V(126, 143.6),
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=V(100, 142.6), toef=V(119, 143.6))
    grip = W + (W - E).n() * 3.4
    piv = V(138, 36)
    ld = (piv - grip).n()
    plate = piv + ld * 22
    back = [
        # estructura: columna, viga superior y base
        rrect(136, 22, 9, FLOOR - 22, 3, "mk"),
        rrect(56, FLOOR - 4, 96, 4, 2, "mk"),
        # asiento
        rrect(78, 120, 6, FLOOR - 120, 2, "mk"),
        rrect(58, 112, 46, 8, 4, "pad"),
        # soporte del rodillo
        line(V(116, 92), V(136, 92), "mkl", 4),
        # palanca lejana
        line(piv + V(-2, -1), grip + V(-2, -1), "mkl", 3),
    ]
    roll = circ(V(116, 92), 6.6, "pad") + circ(V(116, 92), 2, "mk")
    lever = [line(grip, plate + ld * 6, "mkl", 4),
             circ(plate, 14, "pl"), circ(plate, 9.3, "pl2"), circ(plate, 3, "mk"),
             circ(piv, 4.5, "pl"), circ(piv, 1.8, "mk")]
    handle = line(grip + V(-2, -7), grip + V(2, 7), "barl", 2.6)
    fa, nr = person(F, J, {"lats", "biceps", "delt_rear"}, mid_extra=roll,
                    front_extra=circ(grip, 2.2, "bar"))
    body = floor() + "".join(back) + fa + "".join(lever) + handle + nr
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Jalón al pecho en máquina">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')
