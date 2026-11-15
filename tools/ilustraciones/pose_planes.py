"""Ejercicios de las rutinas base que faltaban (potencia, una pierna, cargas, máquinas y movilidad).

Cada función devuelve el SVG de un ejercicio en el mismo estilo de silueta que los demás pose_*.py.
Vista previa: py tools/ilustraciones/pose_planes.py (escribe pose_planes.html con todas).
"""
import math
import os

from silueta_lib import *
from pose_martillo import dumbbell, forearm_ov
from pose_crunch import abs_overlay, hand_on
from pose_plancha import foot_tucked

HERE = os.path.dirname(os.path.abspath(__file__))
MAT = FLOOR - 4


def wrap(F, body, label):
    return f'<svg viewBox="0 0 200 160" role="img" aria-label="{label}"><defs>{"".join(F.defs)}</defs>{body}</svg>'


def feet(A):
    return A + V(-3, 4.1), A + V(16, 5.1)


def joints(S, H, E, W, K, A, heel, toe, Sf, Hf, Ef, Wf, Kf, Af, heelf, toef):
    return dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=heel, toe=toe,
                Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=heelf, toef=toef)


def knee_fwd(a, b): return a if a.x > b.x else b
def knee_up(a, b): return a if a.y < b.y else b
def elbow_back(a, b): return a if a.x < b.x else b
def elbow_down(a, b): return a if a.y > b.y else b


def after_torso(nr, extra):
    """Inserta un recorte sobre el torso cercano (antes de las piernas y el brazo cercanos)."""
    i = nr.find("</g>") + 4
    return nr[:i] + extra + nr[i:]


def torso_ov(F, S, H, fn, cls="m"):
    t = torso_shapes(S, H)[0]
    u = (S - H).n()
    fr = V(-u.y, u.x)
    return F.clip(t, fn(u, fr, cls))


def traps(F, S, H, cls="m"):
    return torso_ov(F, S, H, lambda u, fr, c: [ell(S - u * 1.5 - fr * 6.5, 5, 9.5, u.ang(), c)], cls)


def midback(F, S, H, cls="m"):
    return torso_ov(F, S, H, lambda u, fr, c: [ell(lerp(S, H, 0.24) - fr * 8, 5.5, 9, fr.ang(), c)], cls)


def kettlebell(grip):
    c = grip + V(0, 10.5)
    return (f'<path class="barl" fill="none" stroke-width="2.6" stroke-linecap="round" '
            f'd="M{f(c.x - 5.5)} {f(c.y - 4)}Q{f(c.x - 6)} {f(grip.y - 2.5)} {f(grip.x)} {f(grip.y - 2.5)}'
            f'Q{f(c.x + 6)} {f(grip.y - 2.5)} {f(c.x + 5.5)} {f(c.y - 4)}"/>' + circ(c, 7.8, "pad") +
            rrect(c.x - 6, c.y + 5.5, 12, 3, 1.5, "pad"))


def plate(c, r=19):
    return circ(c, r, "pl") + circ(c, r * 0.71, "pl2") + circ(c, r * 0.22, "mk")


def stack(x, top=96):
    """Pila de pesas con su columna (columna a la derecha de x)."""
    return [rrect(x + 14, 10, 12, FLOOR - 10, 3, "mk"), rrect(x, top, 14, 46, 2, "sk"),
            *[line(V(x + 1, top + 4 + i * 6), V(x + 13, top + 4 + i * 6), "sep", 1) for i in range(7)],
            rrect(x - 4, FLOOR - 4, 34, 4, 2, "mk")]


def far_quads(F, H, K, A, heel, toe, cls="m"):
    th, sh, ft = leg_shapes(H, K, A, heel, toe)
    return leg_overlays(F, H, K, A, th, sh, {"quads"}, cls)


# ---------- cargas y potencia ----------

def carry(one_hand):
    F = Fig("pasomano" if one_hand else "granjero")
    H, S = V(96, 79), V(97, 40)
    A, Af = V(110, 138.5), V(80, 137)
    K = ik(H, A, L_TH, L_SH, knee_fwd)
    Hf = H + V(-2, -1)
    Kf = ik(Hf, Af, L_TH, L_SH, knee_fwd)
    W = S + V(2, 41)
    E = ik(S, W, L_UA, L_FA, elbow_back)
    Sf = S + V(-2, -1)
    Wf = Sf + V(1, 41)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_back)
    heelf, toef = Af + V(-5, 3.5), Af + V(12, 7.8)
    J = joints(S, H, E, W, K, A, *feet(A), Sf, Hf, Ef, Wf, Kf, Af, heelf, toef)
    grip = W + (W - E).n() * 3.4
    gripf = Wf + (Wf - Ef).n() * 3.4
    back = "" if one_hand else dumbbell(gripf, V(1, 0))
    fa, nr = person(F, J, set(), mid_extra=dumbbell(grip, V(1, 0)), front_extra=forearm_ov(F, E, W, "m"))
    if one_hand:
        nr = after_torso(nr, abs_overlay(F, S, H))
        label = "Paseo con una mano"
        fa += forearm_ov(F, Ef, Wf, "t")
    else:
        nr = after_torso(nr, traps(F, S, H))
        label = "Paseo del granjero"
        fa += forearm_ov(F, Ef, Wf, "mf")
    return wrap(F, floor() + back + fa + nr, label)


def granjero():
    return carry(False)


def paseo_una_mano():
    return carry(True)


def kb_swing():
    F = Fig("kbswing")
    A = V(100, 138.5)
    H = V(90, 80)
    K = ik(H, A, L_TH, L_SH, knee_fwd)
    lean = math.radians(-8)
    u = V(math.sin(lean), -math.cos(lean))
    S = H + u * 39
    W = S + V(40, 6)
    E = ik(S, W, L_UA, L_FA, elbow_down)
    Af = A + V(-6, 0)
    Hf = H + V(-2, -1)
    Kf = ik(Hf, Af, L_TH, L_SH, knee_fwd)
    Sf = S + V(-2, -1)
    Wf = W + V(-2, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_down)
    J = joints(S, H, E, W, K, A, *feet(A), Sf, Hf, Ef, Wf, Kf, Af, *feet(Af))
    grip = W + (W - E).n() * 3.4
    fa, nr = person(F, J, {"glutes", "hams"})
    # arco del movimiento
    arc = '<path class="dl" style="stroke:var(--muted);opacity:.6" stroke-dasharray="2 3" d="M118 112Q138 92 136 66"/>'
    return wrap(F, floor() + arc + fa + nr + kettlebell(grip), "Kettlebell swing")


def salto_cajon():
    F = Fig("saltocajon")
    top = 104
    A = V(124, top - 6.5)
    H = V(104, 76)
    K = ik(H, A, L_TH, L_SH, knee_fwd)
    lean = math.radians(34)
    u = V(math.sin(lean), -math.cos(lean))
    S = H + u * 39
    W = S + V(30, 22)
    E = ik(S, W, L_UA, L_FA, elbow_down)
    Af = A + V(-6, 0)
    Hf = H + V(-2, -1)
    Kf = ik(Hf, Af, L_TH, L_SH, knee_fwd)
    Sf = S + V(-2, -1)
    Wf = W + V(-2, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_down)
    J = joints(S, H, E, W, K, A, *feet(A), Sf, Hf, Ef, Wf, Kf, Af, *feet(Af))
    box = [rrect(100, top, 64, FLOOR - top, 4, "sk"), line(V(106, top + 10), V(158, top + 10), "sep", 1)]
    trail = ('<path class="dl" style="stroke:var(--muted);opacity:.6" stroke-dasharray="2 3" fill="none" '
             'd="M54 140Q72 52 110 82"/>')
    fa, nr = person(F, J, {"quads", "glutes", "calves"})
    return wrap(F, floor() + "".join(box) + trail + fa + nr, "Salto al cajón")


# ---------- una pierna ----------

def bulgara():
    F = Fig("bulgara")
    A = V(122, 138.5)
    H = V(96, 100)
    K = ik(H, A, L_TH, L_SH, knee_up)
    S = H + V(5, -38.7)
    W = S + V(3, 41)
    E = ik(S, W, L_UA, L_FA, elbow_back)
    benchy = 108
    Af = V(58, benchy - 5)
    Hf = H + V(-2, -1)
    Kf = ik(Hf, Af, L_TH, L_SH, elbow_down)
    heelf, toef = Af + V(3, -3.5), Af + V(-15, 3.2)
    Sf = S + V(-2, -1)
    Wf = W + V(-2, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_back)
    J = joints(S, H, E, W, K, A, *feet(A), Sf, Hf, Ef, Wf, Kf, Af, heelf, toef)
    grip = W + (W - E).n() * 3.4
    gripf = Wf + (Wf - Ef).n() * 3.4
    bench = [rrect(26, benchy, 46, 8, 4, "pad"), rrect(34, benchy + 8, 6, FLOOR - benchy - 8, 2, "mk"),
             rrect(58, benchy + 8, 6, FLOOR - benchy - 8, 2, "mk"), rrect(26, FLOOR - 4, 46, 4, 2, "mk")]
    fa, nr = person(F, J, {"quads", "glutes"}, mid_extra=dumbbell(grip, V(1, 0)))
    return wrap(F, floor() + "".join(bench) + dumbbell(gripf, V(1, 0)) + fa + nr, "Sentadilla búlgara")


def step_up():
    F = Fig("stepup")
    top = 108
    A = V(118, top - 6)
    H = V(94, 82)
    K = ik(H, A, L_TH, L_SH, knee_fwd)
    lean = math.radians(12)
    u = V(math.sin(lean), -math.cos(lean))
    S = H + u * 39
    W = S + V(2, 41)
    E = ik(S, W, L_UA, L_FA, elbow_back)
    Af = V(74, 134)
    Hf = H + V(-2, -1)
    Kf = ik(Hf, Af, L_TH, L_SH, knee_fwd)
    heelf, toef = Af + V(-3, 2), Af + V(13, 9.5)
    Sf = S + V(-2, -1)
    Wf = W + V(-2, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_back)
    J = joints(S, H, E, W, K, A, *feet(A), Sf, Hf, Ef, Wf, Kf, Af, heelf, toef)
    grip = W + (W - E).n() * 3.4
    gripf = Wf + (Wf - Ef).n() * 3.4
    box = [rrect(102, top, 56, FLOOR - top, 4, "sk")]
    fa, nr = person(F, J, {"quads", "glutes"}, mid_extra=dumbbell(grip, V(1, 0)))
    return wrap(F, floor() + "".join(box) + dumbbell(gripf, V(1, 0)) + fa + nr, "Step up")


def pm_una_pierna():
    F = Fig("pmunapierna")
    A = V(100, 138.5)
    H = V(96, 80)
    K = ik(H, A, L_TH, L_SH, knee_fwd)
    lean = math.radians(80)
    u = V(math.sin(lean), -math.cos(lean))
    S = H + u * 39
    W = S + V(-1, 40.5)
    E = ik(S, W, L_UA, L_FA, elbow_back)
    Hf = H + V(-2, -1)
    ang = math.radians(184)
    Kf = Hf + V(math.cos(ang), math.sin(ang)) * L_TH
    Af = Kf + V(math.cos(ang), math.sin(ang)) * L_SH
    heelf, toef = Af + V(-4, -2), Af + V(1, 15)
    Sf = S + V(-2, -1)
    Wf = Sf + V(-1, 40.5)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_back)
    J = joints(S, H, E, W, K, A, *feet(A), Sf, Hf, Ef, Wf, Kf, Af, heelf, toef)
    grip = W + (W - E).n() * 3.4
    fa, nr = person(F, J, {"hams", "glutes"}, mid_extra=dumbbell(grip, V(1, 0)))
    return wrap(F, floor() + fa + nr, "Peso muerto a una pierna")


def equilibrio():
    F = Fig("equilibrio")
    H, S = V(96, 79), V(97, 40)
    A = V(97, 138.5)
    K = ik(H, A, L_TH, L_SH, knee_fwd)
    Hf = H + V(-2, -1)
    Kf = Hf + V(29, -10)
    Kf = Hf + (Kf - Hf).n() * L_TH
    Af = Kf + V(-4, 31.7)
    heelf, toef = Af + V(-3, 4.1), Af + V(15, 7.5)
    W = S + V(26, 30)
    E = ik(S, W, L_UA, L_FA, elbow_down)
    Sf = S + V(-2, -1)
    Wf = Sf + V(-22, 33)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_down)
    J = joints(S, H, E, W, K, A, *feet(A), Sf, Hf, Ef, Wf, Kf, Af, heelf, toef)
    fa, nr = person(F, J, {"glutes", "calves"})
    return wrap(F, floor() + fa + nr, "Equilibrio en una pierna")


def flexor_cadera():
    F = Fig("flexor")
    H = V(94, 109)
    A = V(130, 138.5)
    K = ik(H, A, L_TH, L_SH, knee_up)
    S = H + V(-3, -38.9)
    W = S + V(8, -40)
    E = ik(S, W, L_UA, L_FA, elbow_back)
    Hf = H + V(-2, -1)
    Kf = Hf + V(-13, 28.1)
    Kf = Hf + (Kf - Hf).n() * L_TH
    Af = Kf + V(-L_SH, -1)
    heelf, toef = Af + V(2, -4.5), Af + V(-15, 2.2)
    Sf = S + V(-2, -1)
    Wf = W + V(-3, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_back)
    J = joints(S, H, E, W, K, A, *feet(A), Sf, Hf, Ef, Wf, Kf, Af, heelf, toef)
    mat = [rrect(26, MAT, 148, FLOOR - MAT, 2, "pad")]
    fa, nr = person(F, J, set())
    fa += far_quads(F, Hf, Kf, Af, heelf, toef, "m")
    return wrap(F, floor() + "".join(mat) + fa + nr, "Estiramiento de flexor de cadera")


# ---------- movilidad ----------

def rotacion_toracica():
    F = Fig("rottorac")
    H = V(72, 102)
    S = H + V(39, 0)
    K = V(72, 135)
    A = V(40, 138)
    heel, toe = A + V(3, -3.5), A + V(-15, 3)
    Sf = S + V(-2, -1)
    Wf = V(Sf.x + 1, MAT - 4.5)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_back)
    E = S + V(-3, -22.8)
    W = E + V(14, 12.8)
    Hf = H + V(-2, -1)
    Kf = K + V(-3, 0)
    Af = A + V(-3, 0)
    J = joints(S, H, E, W, K, A, heel, toe, Sf, Hf, Ef, Wf, Kf, Af, heel + V(-3, 0), toe + V(-3, 0))
    mat = [rrect(24, MAT, 152, FLOOR - MAT, 2, "pad")]
    turn = ('<path class="dl" style="stroke:var(--muted);opacity:.7" stroke-dasharray="2 3" fill="none" '
            f'd="M{f(S.x + 14)} {f(S.y - 6)}Q{f(S.x + 12)} {f(S.y - 30)} {f(E.x - 2)} {f(E.y - 8)}"/>')
    fa, nr = person(F, J, {"delt_rear"}, hoff=1.0)
    nr = after_torso(nr, midback(F, S, H))
    return wrap(F, floor() + "".join(mat) + turn + fa + nr, "Rotación torácica")


def noventa():
    F = Fig("noventa")
    H = V(92, MAT - 6)
    S = H + V(2, -38.9)
    K = V(123, MAT - 5.5)
    A = K + V(-9, -1.5)
    heel, toe = A + V(-2, 3), A + V(-12, 4.5)
    Hf = H + V(-3, -1)
    Kf = V(78, MAT - 5.5)
    Af = Kf + V(-L_SH, 0)
    heelf, toef = Af + V(2, -4), Af + V(-15, 2.5)
    W = V(K.x - 4, K.y - 8)
    E = ik(S, W, L_UA, L_FA, elbow_down)
    Sf = S + V(-2, -1)
    Wf = V(72, MAT - 4)
    Ef = ik(Sf, Wf, L_UA, L_FA, knee_fwd)
    J = joints(S, H, E, W, K, A, heel, toe, Sf, Hf, Ef, Wf, Kf, Af, heelf, toef)
    mat = [rrect(22, MAT, 156, FLOOR - MAT, 2, "pad")]
    fa, nr = person(F, J, {"glutes"})
    return wrap(F, floor() + "".join(mat) + fa + nr, "90/90 de cadera")


def tobillo():
    F = Fig("tobillo")
    wall = 164
    A = V(128, 138.5)
    H = V(106, 112)
    K = ik(H, A, L_TH, L_SH, knee_fwd)
    S = H + V(4, -38.8)
    W = V(wall - 4, 66)
    E = ik(S, W, L_UA, L_FA, elbow_down)
    Hf = H + V(-2, -1)
    Kf = Hf + V(-14, 27.6)
    Kf = Hf + (Kf - Hf).n() * L_TH
    Af = Kf + V(-L_SH, -0.5)
    heelf, toef = Af + V(2, -4.5), Af + V(-15, 2.2)
    Sf = S + V(-2, -1)
    Wf = W + V(0, 6)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_down)
    J = joints(S, H, E, W, K, A, *feet(A), Sf, Hf, Ef, Wf, Kf, Af, heelf, toef)
    back = [rrect(wall, 8, 10, FLOOR - 8, 2, "sk"), rrect(30, MAT, 134, FLOOR - MAT, 2, "pad")]
    fa, nr = person(F, J, {"calves"})
    return wrap(F, floor() + "".join(back) + fa + nr, "Movilidad de tobillo")


# ---------- máquinas y peso libre ----------

def press_inc_barra():
    F = Fig("pressincb")
    ang = math.radians(38)
    u = V(-math.cos(ang), -math.sin(ang))
    fr = V(-u.y, u.x)
    bk = fr * -1
    H = V(104, 106)
    S = H + u * 39
    W = S + V(5, -39)
    E = ik(S, W, L_UA, L_FA, elbow_back)
    A = V(136, 139)
    K = ik(H, A, L_TH, L_SH, knee_up)
    Sf, Wf = S + V(-2, -1), W + V(-2, -1.5)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_back)
    Hf, Af = H + V(-2, -1), V(127, 139)
    Kf = ik(Hf, Af, L_TH, L_SH, knee_up)
    J = joints(S, H, E, W, K, A, A + V(-3, 3.6), A + V(16, 4.6), Sf, Hf, Ef, Wf, Kf, Af, Af + V(-3, 3.6), Af + V(16, 4.6))
    grip = W + (W - E).n() * 3.4
    pa = H + bk * 10.5 + u * 2
    pb = H + bk * 10.5 + u * 62
    rest = [pa, pb, pb + bk * 7, pa + bk * 7]
    mid_rest = lerp(pa, pb, 0.45) + bk * 7
    back = [
        rrect(36, 22, 6, FLOOR - 22, 2, "mk"), rrect(36, 30, 14, 4, 2, "mk"),
        plate(grip),
        rrect(30, FLOOR - 4, 104, 4, 2, "mk"),
        rrect(100, 120, 6, FLOOR - 120, 2, "mk"),
        line(mid_rest, V(mid_rest.x + 6, FLOOR - 3), "mkl", 4),
        rrect(80, 110, 40, 8, 4, "pad"),
        poly(rest, "pad", ' stroke-linejoin="round" stroke-width="5"'),
    ]
    fa, nr = person(F, J, {"chest", "delt_front", "triceps"}, hoff=-1.0, front_extra=circ(grip, 2.4, "bar"))
    return wrap(F, floor() + "".join(back) + fa + nr, "Press inclinado con barra")


def seated_upright(F, W, Wf, hi, back_pad=True):
    H, S = V(82, 106), V(80, 67)
    K = V(113, 104)
    A = V(116, 136)
    Kf, Af = K + V(-3, -1), A + V(-4, 0)
    E = ik(S, W, L_UA, L_FA, elbow_down)
    Sf = S + V(-2, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_down)
    heel, toe = A + V(-3, 5.5), A + V(16, 6.5)
    J = joints(S, H, E, W, K, A, heel, toe, Sf, H + V(-2, -1), Ef, Wf, Kf, Af, heel + V(-4, 0), toe + V(-4, 0))
    back = [rrect(84, 122, 6, FLOOR - 122, 2, "mk"), rrect(58, FLOOR - 4, 52, 4, 2, "mk"),
            rrect(60, 112, 44, 9, 4.5, "pad")]
    if back_pad:
        back += [poly([V(62, 52), V(69, 51), V(72, 110), V(65, 110)], "pad", ' stroke-linejoin="round" stroke-width="5"'),
                 line(V(66, 112), V(66, 122), "mkl", 4)]
    return J, back, E


def press_pecho_maq():
    F = Fig("pressmaq")
    W = V(119, 66)
    J, back, E = seated_upright(F, W, W + V(-2, -1), set())
    grip = W + (W - E).n() * 3.4
    piv = V(78, 22)
    back = stack(18) + back + [line(V(44, 22), V(piv.x, piv.y), "mkl", 5), circ(piv, 4.5, "pl"), circ(piv, 1.6, "mk")]
    lever = line(piv, grip + V(0, -9), "mkl", 4) + line(grip + V(0, -9), grip + V(0, 7), "barl", 3)
    fa, nr = person(F, J, {"chest", "delt_front", "triceps"}, hoff=-1.0)
    return wrap(F, floor() + "".join(back) + fa + lever + nr + circ(grip, 2.3, "bar"), "Press de pecho en máquina")


def jalon_estrecho():
    F = Fig("jalonestr")
    H, S = V(84, 104), V(78, 66)
    W = V(96, 66)
    E = ik(S, W, L_UA, L_FA, elbow_down)
    A = V(114, 139)
    K = ik(H, A, L_TH, L_SH, knee_fwd)
    Sf, Wf = S + V(-2, -1), W + V(-1, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_down)
    Hf, Af = H + V(-2, -1), V(107, 139)
    Kf = ik(Hf, Af, L_TH, L_SH, knee_fwd)
    J = joints(S, H, E, W, K, A, V(111, 142.6), V(130, 143.6), Sf, Hf, Ef, Wf, Kf, Af, V(104, 142.6), V(123, 143.6))
    grip = W + (W - E).n() * 3.4
    pul = V(grip.x + 6, 17)
    vtop = grip + V(2, -9)
    back = [
        rrect(150, 12, 12, FLOOR - 12, 3, "mk"),
        rrect(138, 96, 14, 46, 2, "sk"),
        *[line(V(139, 100 + i * 6), V(151, 100 + i * 6), "sep", 1) for i in range(7)],
        rrect(136, FLOOR - 4, 34, 4, 2, "mk"),
        rrect(pul.x - 2, 11, 162 - pul.x + 2, 6, 3, "mk"),
        line(V(pul.x - 6, 17), vtop, "cab", 1.1),
        circ(pul, 6, "pl"), circ(pul, 2, "mk"),
        rrect(82, 120, 6, FLOOR - 120, 2, "mk"),
        rrect(62, FLOOR - 4, 52, 4, 2, "mk"),
        rrect(62, 112, 46, 8, 4, "pad"),
        line(V(119, 92), V(150, 92), "mkl", 4),
    ]
    roll = circ(V(119, 92), 6.6, "pad") + circ(V(119, 92), 2, "mk")
    vbar = poly([vtop, grip + V(-3, 2), grip + V(5, 2)], "mkl", ' fill="none" stroke-width="2.4" stroke-linejoin="round" style="stroke:var(--muted)"')
    fa, nr = person(F, J, {"lats", "biceps"}, mid_extra=roll)
    return wrap(F, floor() + "".join(back) + fa + vbar + nr + circ(grip, 2.3, "bar"), "Jalón con agarre estrecho")


def triceps_cabeza():
    F = Fig("tricab")
    H, S = V(94, 79), V(96, 41)
    A = V(97, 138.5)
    K = ik(H, A, L_TH, L_SH, knee_fwd)
    Hf, Af = V(92, 78), V(86, 138.5)
    Kf = ik(Hf, Af, L_TH, L_SH, knee_fwd)
    E = S + V(6, -22.2)
    W = E + V(-14.5, 12.3)
    Sf = S + V(-2, -1)
    Ef = Sf + V(6, -22.2)
    Wf = Ef + V(-14.5, 12.3)
    J = joints(S, H, E, W, K, A, *feet(A), Sf, Hf, Ef, Wf, Kf, Af, *feet(Af))
    grip = W + (W - E).n() * 3.4
    fa, nr = person(F, J, {"triceps"})
    return wrap(F, floor() + fa + nr + dumbbell(grip + V(-2, 1), V(0.3, 1)), "Extensión de tríceps sobre la cabeza")


def crunch_polea():
    F = Fig("crunchpolea")
    K = V(92, MAT - 5.5)
    A = V(60, MAT - 6)
    heel, toe = A + V(3, -3.6), A + V(-15, 3.2)
    H = V(90, K.y - 30)
    u = V(0.86, 0.3).n()
    fr = V(-u.y, u.x)
    S = H + u * 39
    hc = S + u * 20 + fr * 2.0
    target = hc - fr * 5 - u * 3
    W = target
    for _ in range(6):
        E = ik(S, W, L_UA, L_FA, knee_up)
        W = target - (W - E).n() * 3.4
    E = ik(S, W, L_UA, L_FA, knee_up)
    Sf, Hf = S + V(-2, -1), H + V(-2, -1)
    Wf, Ef = W + V(-2, -1), E + V(-2, -1)
    Kf, Af = K + V(-3, 0), A + V(-3, 0)
    J = joints(S, H, E, W, K, A, heel, toe, Sf, Hf, Ef, Wf, Kf, Af, heel + V(-3, 0), toe + V(-3, 0))
    pul = V(160, 18)
    back = [rrect(168, 8, 12, FLOOR - 8, 3, "mk"), rrect(154, 11, 16, 10, 2, "mk"), circ(pul, 5.5, "pl"), circ(pul, 1.8, "mk"),
            rrect(30, MAT, 120, FLOOR - MAT, 2, "pad"), rrect(162, FLOOR - 4, 24, 4, 2, "mk")]
    cable = line(V(pul.x - 3.5, pul.y + 4), target, "cab", 1.1)
    fa, nr = person(F, J, set())
    nr = after_torso(nr, abs_overlay(F, S, H))
    return wrap(F, floor() + "".join(back) + cable + fa + nr, "Crunch en polea")


def pallof():
    """Vista de frente: el cable tira hacia el lado y el core resiste la rotación."""
    F = Fig("pallof")
    from pose_laterales import torso_front, foot, mir
    CX = 100
    S = V(85, 41)
    H, K, A = V(92.5, 80), V(89, 110.5), V(86, 138)
    hands = V(CX + 1, 58)
    sides = []
    for s in (-1, 1):
        S_ = S if s < 0 else mir(S)
        E_ = V(CX + s * 9, 64)
        sides.append((S_, E_, hands + V(s * 1.6, 0), H if s < 0 else mir(H), K if s < 0 else mir(K), A if s < 0 else mir(A), s))
    t = [torso_front()]
    hc = V(CX, 19.5)
    head = [cap(V(CX, 32), 5.6, V(CX, 24), 4.6), ell(hc, 7.6, 8.8, 0)]
    trp = [cap(V(91, 33), 3.5, V(84, 37.5), 4.5), cap(V(109, 33), 3.5, V(116, 37.5), 4.5)]
    legs, arms = [], []
    for S_, E_, W_, H_, K_, A_, s in sides:
        legs += [outline(H_, K_, TH_A, TH_P), circ(K_, 5.2), outline(K_, A_, SH_A, SH_P)] + foot(A_, s)
        arms += [outline(S_, E_, UA_A, UA_P), circ(E_, 3.6), outline(E_, W_, FA_A, FA_P)]
    pul = V(176, 58)
    back = [rrect(180, 10, 10, FLOOR - 10, 3, "mk"), rrect(172, 50, 10, 16, 2, "mk"), circ(pul, 4.5, "pl"),
            rrect(170, FLOOR - 4, 26, 4, 2, "mk")]
    body = [f'<g class="b">{"".join(legs)}</g>',
            f'<g class="halo">{"".join(t + trp)}</g><g class="b">{"".join(t + trp + head)}</g>']
    core = [ell(V(100, 66), 10, 13, 0, "m"), ell(V(88, 70), 4.5, 10, -8, "m"), ell(V(112, 70), 4.5, 10, 8, "m"),
            '<path class="dl" d="M100 54L100 78"/>', '<path class="dl" d="M90 79Q95 86 100 87Q105 86 110 79"/>',
            ell(V(92, 46.5), 7.8, 5.6, 8, "t"), ell(V(108, 46.5), 7.8, 5.6, -8, "t")]
    body.append(F.clip(t, core))
    body.append(f'<g class="halo">{"".join(arms)}</g><g class="b">{"".join(arms)}</g>')
    grip = [circ(hands, 4.6, "b"), rrect(hands.x - 2, hands.y - 7, 4, 14, 2, "bar")]
    cable = line(hands + V(2, 0), V(pul.x - 3, pul.y), "cab", 1.1)
    arrow = '<path class="dl" style="stroke:var(--muted);opacity:.7" fill="none" d="M126 46L146 46M141 42L146 46L141 50"/>'
    return wrap(F, floor() + "".join(back) + "".join(body) + cable + "".join(grip) + arrow, "Pallof press")


def hip_thrust():
    F = Fig("hipthrust")
    benchy = 100
    H = V(108, 94)
    S = V(70, benchy - 7)
    A = V(136, 138.5)
    K = ik(H, A, L_TH, L_SH, knee_up)
    u = (S - H).n()
    fr = V(-u.y, u.x)
    bar = H + fr * 12 + u * 1
    target = bar + V(-3, 2)
    W = target
    for _ in range(6):
        E = ik(S, W, L_UA, L_FA, knee_up)
        W = target - (W - E).n() * 3.4
    E = ik(S, W, L_UA, L_FA, knee_up)
    Hf, Af = H + V(-2, -1), A + V(-7, 0)
    Kf = ik(Hf, Af, L_TH, L_SH, knee_up)
    Sf = S + V(-2, -1)
    Wf, Ef = W + V(-2, -1), E + V(-2, -1)
    J = joints(S, H, E, W, K, A, *feet(A), Sf, Hf, Ef, Wf, Kf, Af, *feet(Af))
    bench = [rrect(18, benchy, 58, 9, 4.5, "pad"), rrect(26, benchy + 9, 6, FLOOR - benchy - 9, 2, "mk"),
             rrect(62, benchy + 9, 6, FLOOR - benchy - 9, 2, "mk"), rrect(18, FLOOR - 4, 58, 4, 2, "mk")]
    fa, nr = person(F, J, {"glutes", "hams"}, hoff=-1.0)
    return wrap(F, floor() + "".join(bench) + plate(bar) + fa + nr + circ(bar, 2.4, "bar"), "Hip thrust")


def prensa():
    F = Fig("prensa")
    H = V(84, 114)
    u = V(-0.62, -0.78).n()
    S = H + u * 39
    A = V(118, 80)
    K = ik(H, A, L_TH, L_SH, knee_up)
    rail = V(0.62, -0.78).n()
    pn = rail * -1
    pd = pn.perp()
    heel, toe = A + pd * (-3.5) + pn * 4, A + pd * 14 + pn * 5.5
    if heel.y < toe.y:
        pd = pd * -1
        heel, toe = A + pd * (-3.5) + pn * 4, A + pd * 14 + pn * 5.5
    Hf, Af = H + V(-2, -1), A + V(-3, -1)
    Kf = ik(Hf, Af, L_TH, L_SH, knee_up)
    W = H + V(12, 6)
    E = ik(S, W, L_UA, L_FA, elbow_back)
    Sf = S + V(-2, -1)
    Wf, Ef = W + V(-2, -1), E + V(-2, -1)
    J = joints(S, H, E, W, K, A, heel, toe, Sf, Hf, Ef, Wf, Kf, Af, heel + V(-3, -1), toe + V(-3, -1))
    fr = V(-u.y, u.x)
    bk = fr * -1
    pa, pb = H + bk * 10 + u * (-8), H + bk * 10 + u * 50
    seat = poly([pa, pb, pb + bk * 7, pa + bk * 7], "pad", ' stroke-linejoin="round" stroke-width="5"')
    sole_c = lerp(heel, toe, 0.5) + pn * 4.5
    plat = poly([sole_c - pd * 16, sole_c + pd * 16, sole_c + pd * 16 + pn * 5, sole_c - pd * 16 + pn * 5], "pad",
                ' stroke-linejoin="round" stroke-width="3"')
    r0 = sole_c + pn * 6
    back = [line(V(60, FLOOR - 3), V(176, FLOOR - 3) + V(0, 0), "mkl", 4),
            line(V(96, 138), V(178, 34), "mkl", 5), line(V(176, 34), V(176, FLOOR - 3), "mkl", 5),
            line(r0, r0 + rail * 20, "mkl", 4), plate(r0 + rail * 16 + pn * 2, 14),
            line(lerp(pa, pb, 0.3) + bk * 7, V(lerp(pa, pb, 0.3).x + 10, FLOOR - 3), "mkl", 4),
            seat, plat]
    fa, nr = person(F, J, {"quads", "glutes"}, hoff=-1.0)
    return wrap(F, floor() + "".join(back) + fa + nr, "Prensa")


def talones_sentado():
    F = Fig("talsent")
    H, S = V(80, 104), V(76, 66)
    K = V(112, 102)
    A = V(115, 131)
    heel, toe = A + V(-2.5, 3.5), A + V(17, 9.5)
    Kf, Af = K + V(-3, -1), A + V(-4, 0)
    W = V(103, 88)
    E = ik(S, W, L_UA, L_FA, elbow_down)
    Sf = S + V(-2, -1)
    Wf = W + V(-2, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, elbow_down)
    J = joints(S, H, E, W, K, A, heel, toe, Sf, H + V(-2, -1), Ef, Wf, Kf, Af, heel + V(-4, 0), toe + V(-4, 0))
    padc = V(104, 91)
    back = [rrect(62, 112, 40, 9, 4.5, "pad"), rrect(78, 121, 6, FLOOR - 121, 2, "mk"), rrect(56, FLOOR - 4, 110, 4, 2, "mk"),
            rrect(122, 138, 22, 5, 2, "sk"),
            line(V(150, 88), V(150, FLOOR - 3), "mkl", 5), line(padc + V(10, 0), V(150, 88), "mkl", 4),
            plate(V(150, 76), 12)]
    mid = rrect(padc.x - 13, padc.y - 4.5, 26, 9, 4.5, "pad")
    fa, nr = person(F, J, {"calves"}, mid_extra=mid)
    return wrap(F, floor() + "".join(back) + fa + nr, "Elevación de talones sentado")


POSES = {
    "Paseo del granjero": granjero,
    "Paseo con una mano": paseo_una_mano,
    "Kettlebell swing": kb_swing,
    "Salto al cajón": salto_cajon,
    "Sentadilla búlgara": bulgara,
    "Step up": step_up,
    "Peso muerto a una pierna": pm_una_pierna,
    "Equilibrio en una pierna": equilibrio,
    "Estiramiento de flexor de cadera": flexor_cadera,
    "Rotación torácica": rotacion_toracica,
    "90/90 de cadera": noventa,
    "Movilidad de tobillo": tobillo,
    "Press inclinado con barra": press_inc_barra,
    "Press de pecho en máquina": press_pecho_maq,
    "Jalón con agarre estrecho": jalon_estrecho,
    "Extensión de tríceps sobre la cabeza": triceps_cabeza,
    "Crunch en polea": crunch_polea,
    "Pallof press": pallof,
    "Hip thrust": hip_thrust,
    "Prensa": prensa,
    "Elevación de talones sentado": talones_sentado,
}


if __name__ == "__main__":
    import sys
    pick = sys.argv[1:] or list(POSES)
    figs = "".join(f"<figure>{POSES[name]()}<figcaption>{name}</figcaption></figure>" for name in pick)
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Ejercicios de los planes</title>'
            f'<style>{CSS}</style></head><body><div class="grid">{figs}</div></body></html>')
    open(os.path.join(HERE, "pose_planes.html"), "w", encoding="utf-8").write(html)
    print(len(POSES), "poses")
