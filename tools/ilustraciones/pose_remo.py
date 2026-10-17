from silueta_lib import *

D = __import__("os").path.dirname(__import__("os").path.abspath(__file__))


def draw():
    F = Fig("remo")
    H, S = V(80, 104), V(89, 66.5)
    W = V(96, 88)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    A = V(114, 139)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.y < b.y else b)
    Sf, Wf = V(87, 65.5), V(94, 87)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    Hf, Af = V(78, 103), V(107, 139)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.y < b.y else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=V(111, 142.6), toe=V(130, 143.6),
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=V(104, 142.6), toef=V(123, 143.6))
    u = (S - H).n()
    fr = V(-u.y, u.x)
    grip = W + (W - E).n() * 3.4
    piv = V(150, 30)
    ld = (grip - piv).n()
    plate = piv + ld * 34 - ld.perp() * 11
    # apoyo de pecho paralelo al torso
    pc = S - u * 13 + fr * 17.8
    pad = [pc + u * 15, pc + u * 15 + fr * 6, pc - u * 15 + fr * 6, pc - u * 15]
    back = [
        # columna y base
        rrect(146, 22, 10, FLOOR - 22, 3, "mk"),
        rrect(56, FLOOR - 4, 112, 4, 2, "mk"),
        # soporte del pecho
        line(lerp(pad[1], pad[2], 0.5), V(146, lerp(pad[1], pad[2], 0.5).y + 2), "mkl", 4),
        # asiento
        rrect(78, 120, 6, FLOOR - 120, 2, "mk"),
        rrect(60, 112, 40, 8, 4, "pad"),
        # palanca lejana
        line(piv + V(-2, 0), grip + V(-2, -1), "mkl", 3),
        line(grip + V(-2, -7), grip + V(-2, 6), "mkl", 3),
    ]
    chest_pad = poly(pad, "pad", ' stroke-linejoin="round" stroke-width="4"')
    t = torso_shapes(S, H, 1.0)[0]
    lats_low = F.clip(t, [ell(lerp(S, H, 0.62) - fr * 8.5, 5.5, 10, fr.ang(), "m")])
    lever = [line(piv, plate, "mkl", 4), circ(plate, 14, "pl"), circ(plate, 9.3, "pl2"), circ(plate, 3, "mk"),
             line(piv, grip, "mkl", 3.4), circ(piv, 4.5, "pl"), circ(piv, 1.8, "mk")]
    handle = line(grip + V(0.6, -8), grip + V(-0.6, 7.5), "barl", 2.6)
    fa, nr = person(F, J, {"lats", "biceps", "delt_rear"}, hoff=1.0,
                    mid_extra=lats_low + chest_pad + handle)
    body = floor() + "".join(back) + fa + "".join(lever) + nr
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Remo en máquina">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Remo</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}</figure></body></html>')
    open(D + r"\pose_remo.html", "w", encoding="utf-8").write(html)
