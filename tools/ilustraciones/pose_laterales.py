"""Elevaciones laterales: figura de frente, brazos abiertos a la altura del hombro."""
import os

from silueta_lib import *

OUT_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pose_laterales.html")

CX = 100


def mir(p):
    return V(2 * CX - p.x, p.y)


def torso_front():
    """Torso de frente (mitad izquierda del dibujo, espejada)."""
    half = [V(100, 31), V(93.5, 32.5), V(86, 35.5), V(81.5, 40), V(82.5, 47), V(84.5, 56), V(87.5, 66),
            V(88.5, 73), V(87.5, 80), V(90, 86)]
    pts = half + [mir(p) for p in reversed(half)]
    return smooth(pts)


def foot(A, s):
    """Pie visto de frente: empeine corto hacia afuera."""
    return [cap(A, 3.3, A + V(s * 2.5, 6.2), 3.2), ell(A + V(s * 2.2, 6.6), 4.6, 2.7, 0)]


def dumbbell_end(c):
    """Mancuerna vista casi de punta: dos cabezas superpuestas y el mango corto."""
    out = [line(c + V(0, -6), c + V(0, 6), "barl", 2.4)]
    for dy in (-6.5, 6.5):
        out.append(rrect(c.x - 5.6, c.y + dy - 2.6, 11.2, 5.2, 1.6, "pad", ' stroke-width="1.6"'))
    return "".join(out)


def draw():
    F = Fig("laterales")
    S = V(85, 41)
    E = S + V(-22.6, 3.5)
    W = E + V(-18.7, 2.5)
    H, K, A = V(92.5, 80), V(91, 110.5), V(91, 138)
    sides = [(S, E, W, H, K, A, -1), (mir(S), mir(E), mir(W), mir(H), mir(K), mir(A), 1)]
    t = [torso_front()]
    hc = V(CX, 19.5)
    head = [cap(V(CX, 32), 5.6, V(CX, 24), 4.6), ell(hc, 7.6, 8.8, 0)]
    traps = [cap(V(91, 33), 3.5, V(84, 37.5), 4.5), cap(V(109, 33), 3.5, V(116, 37.5), 4.5)]
    legs, arms, hands, uppers, bells = [], [], [], [], []
    for S_, E_, W_, H_, K_, A_, s in sides:
        th = outline(H_, K_, TH_A, TH_P)
        sh = outline(K_, A_, SH_A, SH_P)
        legs += [th, circ(K_, 5.2), sh] + foot(A_, s)
        sh_, hand = arm_shapes(S_, E_, W_)
        arms += sh_
        hands += hand
        uppers.append(sh_[0])
        bells.append(dumbbell_end(W_ + (W_ - E_).n() * 3.4))
    body = []
    body.append(f'<g class="b">{"".join(legs)}</g>')
    body.append(f'<g class="halo">{"".join(t + traps)}</g><g class="b">{"".join(t + traps + head)}</g>')
    # pecho, abdomen y línea de las caderas en tono de definición
    defs = [ell(V(92, 46.5), 7.8, 5.6, 8, "t"), ell(V(108, 46.5), 7.8, 5.6, -8, "t"),
            '<path class="dl" d="M100 54L100 76"/>',
            '<path class="dl" d="M90 79Q95 86 100 87Q105 86 110 79"/>']
    body.append(F.clip(t, defs))
    body.append(f'<g class="halo">{"".join(arms + hands)}</g>')
    body.extend(bells)
    body.append(f'<g class="b">{"".join(arms + hands)}</g>')
    # deltoide lateral: la tapa del hombro
    for (S_, E_, W_, *_), up in zip(sides, uppers):
        d = (E_ - S_).n()
        ov = [ell(S_ + d * 3.5 + V(0, -1.5), 8.5, 6.4, d.ang(), "m")]
        body.append(F.clip([up] + [cap(S_, 6, S_ + V(0, 0), 6)], ov))
    # bíceps en tono de definición para dar volumen al brazo
    for (S_, E_, W_, *_), up in zip(sides, uppers):
        body.append(F.clip([up], [ell(lerp(S_, E_, 0.62) + V(0, 3), 7, 3, (E_ - S_).ang(), "t")]))
    svg_body = floor() + "".join(body)
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Elevaciones laterales">'
            f'<defs>{"".join(F.defs)}</defs>{svg_body}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Elevaciones laterales</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}</figure></body></html>')
    open(OUT_HTML, "w", encoding="utf-8").write(html)
