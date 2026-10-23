"""Plancha lateral sobre el antebrazo, vista de frente, en estilo silueta."""
from silueta_lib import *
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MAT = FLOOR - 4


def draw():
    F = Fig("planchalat")
    th = math.radians(17.5)
    u = V(math.cos(th), -math.sin(th))      # de los pies a la cabeza
    w = V(-math.sin(th), -math.cos(th))     # hacia el costado de arriba
    O = V(40, MAT + 0.2) + w * 6.5      # borde del pie de abajo sobre la colchoneta
    P = lambda a, b: O + u * a + w * b

    # piernas: dos piernas juntas, una sobre la otra
    legs = []
    for s in (1, -1):
        hip, knee, ank = P(66, 6.0 * s), P(35, 3.8 * s), P(5, 3.0 * s)
        legs.append([cap(hip, 6.6, knee, 4.4), circ(knee, 4.4), cap(knee, 4.6, ank, 2.6),
                     ell(P(2.5, 3.2 * s + 1.0 * s), 4.6, 3.2, u.ang() - 20 * s)])

    # torso de frente: hombros anchos, cintura, cadera
    tpts = [P(64, -12.5), P(74, -11.2), P(84, -10.4), P(94, -13.8), P(103, -15.2), P(107, -12),
            P(109.5, -4), P(109.5, 4), P(107, 12), P(103, 15.2), P(94, 13.8), P(84, 10.4),
            P(74, 11.2), P(64, 12.5), P(58, 6), P(57, 0), P(58, -6)]
    torso = [smooth(tpts)]
    neck = cap(P(106, 0), 4.6, P(114, 0), 4.0)
    hc = P(121.5, 0)
    head = ell(hc, 8.6, 7.2, u.ang())

    # brazo de abajo: hombro sobre el codo, antebrazo apoyado hacia adelante
    Sl = P(103, -11.5)
    El = V(Sl.x + 1, MAT - 4.2)
    Wl = El + V(13, 0.6)
    arm_lo = [cap(Sl, 5.6, El, 4.0), circ(El, 4.0), cap(El, 4.0, Wl, 2.8), circ(Wl + V(2.4, -0.3), 3.6)]

    # brazo de arriba: extendido hacia el techo
    Su = P(103, 11.5)
    Eu = Su + V(0.3, -L_UA)
    Wu = Eu + V(0.2, -L_FA)
    arm_up = [cap(Su, 5.6, Eu, 4.0), circ(Eu, 3.9), cap(Eu, 4.0, Wu, 2.6), ell(Wu + V(0, -3.6), 3.0, 4.4, 90)]

    ov = []
    # oblicuos: franja lateral de la cintura en ambos costados
    for s in (1, -1):
        ov.append(ell(P(80, 9.0 * s), 15, 4.6, u.ang() - 8 * s, "m"))
    dl = []
    for s in (1, -1):
        for k in (72, 79, 86):
            a, b = P(k, 6.0 * s), P(k + 6, 11.0 * s)
            dl.append(f'<path class="dl" d="M{f(a.x)} {f(a.y)}L{f(b.x)} {f(b.y)}"/>')
    a, b = P(64, 0), P(92, 0)
    dl.append(f'<path class="dl" d="M{f(a.x)} {f(a.y)}L{f(b.x)} {f(b.y)}"/>')

    back = [rrect(22, MAT, 156, FLOOR - MAT, 2, "pad")]
    body = [
        f'<g class="b">{"".join(legs[1])}</g>',
        f'<g class="halo">{"".join(legs[0])}</g><g class="b">{"".join(legs[0])}</g>',
        f'<g class="b">{"".join(arm_lo)}</g>',
        f'<g class="b">{neck}{head}</g>',
        f'<g class="halo">{"".join(torso)}</g><g class="b">{"".join(torso)}</g>',
        F.clip(torso, ov + dl),
        f'<g class="halo">{"".join(arm_up)}</g><g class="b">{"".join(arm_up)}</g>',
    ]
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Plancha lateral">'
            f'<defs>{"".join(F.defs)}</defs>{floor()}{"".join(back)}{"".join(body)}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Plancha lateral</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}'
            f'<figcaption>Plancha lateral</figcaption></figure></body></html>')
    open(os.path.join(HERE, "pose_planchalat.html"), "w", encoding="utf-8").write(html)
