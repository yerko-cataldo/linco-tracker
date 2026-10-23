"""Press militar: de pie, barra subiendo por delante de la cabeza."""
import os

from silueta_lib import *

OUT_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pose_militar.html")


def draw():
    F = Fig("militar")
    H, S = V(94, 79), V(94, 41)
    A = V(95, 138.5)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    Hf, Af = V(92, 78), V(89, 138.5)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    # brazos: barra por encima de la frente, codos adelante y abajo
    W = V(110, 15)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.x > b.x else b)
    Sf = S + V(-2, -1)
    Wf = W + V(-2, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.x > b.x else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=A + V(-3, 4.1), toe=A + V(16, 5.1),
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=Af + V(-3, 4.1), toef=Af + V(16, 5.1))
    grip = W + (W - E).n() * 3.4
    bar = grip + V(-0.6, 0.6)
    back = [circ(bar, 11.5, "pl"), circ(bar, 7.8, "pl2"), circ(bar, 3.2, "mk")]
    fa, nr = person(F, J, {"delt_front", "triceps"}, front_extra=circ(bar, 2.4, "bar"))
    body = floor() + "".join(back) + fa + nr
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Press militar">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Press militar</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}</figure></body></html>')
    open(OUT_HTML, "w", encoding="utf-8").write(html)
