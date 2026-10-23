"""Aductores en máquina: vista frontal, sentado, almohadillas por dentro de las rodillas.

El movimiento es lateral, así que la figura va de frente. Este módulo también arma la figura
frontal que usa pose_abductores.py (front_seated)."""
import os

from silueta_lib import *

HERE = os.path.dirname(os.path.abspath(__file__))
CX = 100.0


def mir(p, s):
    """Punto p (relativo al centro) en el lado s (1 derecha, -1 izquierda)."""
    return V(CX + s * p.x, p.y)


TORSO = [V(6, 53), V(13, 56.5), V(19, 60), V(21.5, 66), V(19.5, 76), V(15.5, 86), V(14.5, 94), V(16.5, 103), V(9, 109.5), V(0, 110)]


def torso_front():
    right = [mir(p, 1) for p in TORSO]
    left = [mir(p, -1) for p in reversed(TORSO[:-1])]
    return smooth(right[:-1] + [V(CX, 110)] + left[1:] + [mir(TORSO[0], -1)])


def front_seated(F, dx, pads_inside, hi, label):
    """Figura sentada de frente con las rodillas a ±dx del centro."""
    sides = (-1, 1)
    J = {}
    for s in sides:
        J[s] = dict(S=mir(V(20, 64), s), E=mir(V(24.5, 85), s), W=mir(V(26, 100), s),
                    H=mir(V(9.5, 104), s), K=mir(V(dx, 110), s), A=mir(V(dx + 1, 137.5), s))
    # aparato detrás
    stack = [rrect(16, 26, 12, FLOOR - 26, 3, "mk"), rrect(28, 96, 14, 46, 2, "sk"),
             *[line(V(29, 100 + i * 6), V(41, 100 + i * 6), "sep", 1) for i in range(7)],
             rrect(12, FLOOR - 4, 40, 4, 2, "mk")]
    back = stack + [
        line(V(28, 60), V(74, 60), "mkl", 4),
        rrect(74, 46, 52, 64, 7, "pad"),
        rrect(96, 112, 8, FLOOR - 112, 2, "mk"),
        rrect(62, FLOOR - 4, 76, 4, 2, "mk"),
        rrect(64, 104, 72, 10, 5, "pad"),
    ]
    # mangos a los lados del asiento
    for s in sides:
        g = J[s]["W"] + V(0, 3)
        back.append(line(g + V(0, -6), g + V(0, 9), "mkl", 3.5))

    torso = torso_front()
    hc = V(CX, 40)
    head = [ell(hc, 7.6, 9.0, 0), cap(V(CX, 47), 4.6, V(CX, 57), 5.4),
            circ(V(CX - 7.4, 41), 1.8), circ(V(CX + 7.4, 41), 1.8)]
    delts = [circ(mir(V(19.5, 64.5), s), 6.4) for s in sides]
    body = [f'<g class="b">{torso}{"".join(head)}{"".join(delts)}</g>']
    # pecho y abdomen sutiles
    body.append(F.clip([torso], [ell(mir(V(8.5, 69), s), 8.5, 6.5, 0, "t") for s in sides]))

    legs, leg_shp = [], {}
    for s in sides:
        j = J[s]
        th = [cap(j["H"], 9.2, j["K"], 6.8)]
        sh = [outline(j["K"], j["A"], SH_A, SH_P), circ(j["K"], 6.2)]
        ft = [cap(j["A"], 3.4, j["A"] + V(0, 4.2), 4.3)]
        leg_shp[s] = (th, sh, ft)
        shapes = "".join(th + sh + ft)
        legs.append(f'<g class="halo">{shapes}</g><g class="b">{shapes}</g>')
        legs.append(F.clip(sh, [ell(lerp(j["K"], j["A"], 0.35) + V(-s * 2.2, 0), 3.2, 8, 0, "t")]))
        legs.append(ell(j["K"] + V(0, 0.5), 3.4, 4.2, 0, "t"))
    arms = []
    for s in sides:
        j = J[s]
        arm, hand = arm_shapes(j["S"], j["E"], j["W"])
        shapes = "".join(arm + hand)
        arms.append(f'<g class="halo">{shapes}</g><g class="b">{shapes}</g>')
        arms.append(F.clip(arm[:1], [ell(lerp(j["S"], j["E"], 0.1), 6.0, 7.0, (j["E"] - j["S"]).ang(), "t")]))

    hl = []
    for s in sides:
        j = J[s]
        th = leg_shp[s][0]
        if "adductors" in hi:
            d = (j["K"] - j["H"])
            inner = d.n().perp() * (s * 1.0)
            if inner.x * s > 0:
                inner = inner * -1
            hl.append(F.clip(th, [ell(lerp(j["H"], j["K"], 0.42) + inner * 5, d.len() * 0.6, 5.6, d.ang(), "m")]))
        if "abductors" in hi:
            hl.append(F.clip([torso] + th, [ell(mir(V(17, 101), s), 5.4, 9, s * -20, "m")]))

    # almohadillas de las rodillas con su brazo de palanca
    pads = []
    for s in sides:
        k = J[s]["K"]
        px = k.x + s * (-9.6 if pads_inside else 10.5)
        piv = V(CX + s * 5, 126)
        pads.append(line(V(px, k.y + 4), piv, "mkl", 3.4))
        top = k.y - 3 if pads_inside else k.y - 10
        pads.append(rrect(px - 3, top, 6, 20, 3, "pad"))
    pads.append(circ(V(CX, 126), 5, "pl"))
    pads.append(circ(V(CX, 126), 1.8, "mk"))

    if pads_inside:
        order = arms + legs + hl + pads
    else:
        order = arms + legs + hl + pads
    svg_body = floor() + "".join(back) + "".join(body) + "".join(order)
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="{label}">'
            f'<defs>{"".join(F.defs)}</defs>{svg_body}</svg>')


def draw():
    return front_seated(Fig("aductores"), 30, True, {"adductors"}, "Aductores en máquina")


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Aductores en máquina</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}</figure></body></html>')
    open(os.path.join(HERE, "pose_aductores.html"), "w", encoding="utf-8").write(html)
