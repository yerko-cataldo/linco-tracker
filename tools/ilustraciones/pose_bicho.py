"""Bicho muerto en estilo silueta."""
from silueta_lib import *
from pose_crunchinv import abs_overlay
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MAT = FLOOR - 4


def arm_dir(S, deg, l=L_UA + L_FA - 0.6):
    a = math.radians(deg)
    W = S + V(math.cos(a), math.sin(a)) * l
    E = ik(S, W, L_UA, L_FA, lambda p, q: p if p.y < q.y else q)
    return E, W


def draw():
    F = Fig("bicho")
    hoff = -2.0
    S, H = V(70, 131), V(109, 130.5)
    # brazo cercano extendido hacia atrás, sobre la cabeza
    E, W = arm_dir(S, -150)
    # pierna cercana en 90/90: muslo vertical, canilla horizontal
    K = H + V(1, -L_TH)
    A = K + V(L_SH, 1)
    heel = A + V(2.4, 2.6)
    toe = A + V(4, -14)
    # lado lejano: brazo vertical, pierna extendida cerca del suelo
    Sf, Hf = S + V(-2, -1), H + V(-2, -1)
    Ef, Wf = arm_dir(Sf, -88)
    a = math.radians(-5)
    dl = V(math.cos(a), math.sin(a))
    Kf = Hf + dl * L_TH
    Af = Kf + dl * L_SH
    anf = dl.perp() * -1
    heelf = Af - anf * 2.6 + dl * 1.5
    toef = Af + dl * 12 + anf * 5
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=heel, toe=toe,
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=heelf, toef=toef)
    back = [rrect(16, MAT, 168, FLOOR - MAT, 2, "pad")]
    fa, nr = person(F, J, set(), hoff=hoff)
    i = nr.index("</g>") + 4
    nr = nr[:i] + abs_overlay(F, S, H, hoff) + nr[i:]
    return (f'<svg viewBox="0 0 200 160" role="img" aria-label="Bicho muerto">'
            f'<defs>{"".join(F.defs)}</defs>{floor()}{"".join(back)}{fa}{nr}</svg>')


if __name__ == "__main__":
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Bicho muerto</title>'
            f'<style>{CSS}</style></head><body><figure style="width:600px">{draw()}'
            f'<figcaption>Bicho muerto</figcaption></figure></body></html>')
    open(os.path.join(HERE, "pose_bicho.html"), "w", encoding="utf-8").write(html)
