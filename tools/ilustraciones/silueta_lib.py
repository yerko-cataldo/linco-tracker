import math

OUT = __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "silueta.html")

L_UA, L_FA, L_TH, L_SH = 23.0, 19.0, 31.0, 32.0


class V:
    def __init__(s, x, y): s.x, s.y = float(x), float(y)
    def __add__(s, o): return V(s.x + o.x, s.y + o.y)
    def __sub__(s, o): return V(s.x - o.x, s.y - o.y)
    def __mul__(s, k): return V(s.x * k, s.y * k)
    def len(s): return math.hypot(s.x, s.y)
    def n(s):
        l = s.len() or 1
        return V(s.x / l, s.y / l)
    def perp(s): return V(-s.y, s.x)
    def ang(s): return math.degrees(math.atan2(s.y, s.x))


def lerp(a, b, t): return a + (b - a) * t
def f(v): return f"{v:.1f}".rstrip("0").rstrip(".")


def circ(c, r, cls=""):
    a = f' class="{cls}"' if cls else ""
    return f'<circle{a} cx="{f(c.x)}" cy="{f(c.y)}" r="{f(r)}"/>'


def ell(c, rx, ry, deg, cls=""):
    a = f' class="{cls}"' if cls else ""
    return f'<ellipse{a} cx="{f(c.x)}" cy="{f(c.y)}" rx="{f(rx)}" ry="{f(ry)}" transform="rotate({f(deg)} {f(c.x)} {f(c.y)})"/>'


def cap(a, ra, b, rb, cls=""):
    d = b - a
    L = d.len()
    if L <= abs(ra - rb) + 0.01:
        return circ(a if ra > rb else b, max(ra, rb), cls)
    phi = math.atan2(d.y, d.x)
    al = math.acos((ra - rb) / L)
    p = lambda c, r, t: V(c.x + r * math.cos(t), c.y + r * math.sin(t))
    A1, B1, B2, A2 = p(a, ra, phi + al), p(b, rb, phi + al), p(b, rb, phi - al), p(a, ra, phi - al)
    lb = 1 if 2 * al > math.pi else 0
    la = 1 if (2 * math.pi - 2 * al) > math.pi else 0
    c = f' class="{cls}"' if cls else ""
    return (f'<path{c} d="M{f(A1.x)} {f(A1.y)}L{f(B1.x)} {f(B1.y)}A{f(rb)} {f(rb)} 0 {lb} 0 {f(B2.x)} {f(B2.y)}'
            f'L{f(A2.x)} {f(A2.y)}A{f(ra)} {f(ra)} 0 {la} 0 {f(A1.x)} {f(A1.y)}Z"/>')


def ik(a, c, l1, l2, pick):
    d = (c - a).len()
    D = min(d, l1 + l2 - 0.05)
    x = (l1 * l1 - l2 * l2 + D * D) / (2 * D)
    h = math.sqrt(max(0.0, l1 * l1 - x * x))
    u = (c - a).n()
    p = a + u * x
    nn = u.perp()
    return pick(p + nn * h, p + nn * (-h))


def poly(pts, cls, extra=""):
    s = " ".join(f"{f(p.x)},{f(p.y)}" for p in pts)
    return f'<polygon class="{cls}" points="{s}"{extra}/>'


def rrect(x, y, w, h, r, cls, extra=""):
    return f'<rect class="{cls}" x="{f(x)}" y="{f(y)}" width="{f(w)}" height="{f(h)}" rx="{f(r)}"{extra}/>'


def line(a, b, cls, w):
    return f'<line class="{cls}" x1="{f(a.x)}" y1="{f(a.y)}" x2="{f(b.x)}" y2="{f(b.y)}" stroke-width="{f(w)}" stroke-linecap="round"/>'


def path(d, cls, extra=""):
    return f'<path class="{cls}" d="{d}"{extra}/>'


def smooth(pts, closed=True, cls=""):
    n = len(pts)
    d = f"M{f(pts[0].x)} {f(pts[0].y)}"
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed or i > 0 else pts[i]
        p1, p2 = pts[i], pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed or i + 2 < n else p2
        c1 = p1 + (p2 - p0) * (1 / 6)
        c2 = p2 - (p3 - p1) * (1 / 6)
        d += f"C{f(c1.x)} {f(c1.y)} {f(c2.x)} {f(c2.y)} {f(p2.x)} {f(p2.y)}"
    if closed:
        d += "Z"
    c = f' class="{cls}"' if cls else ""
    return f'<path{c} d="{d}"/>'


def outline(a, b, antp, postp):
    L = (b - a).len()
    d = (b - a).n()
    an = d.perp() * -1
    pts = [a + d * (t * L) + an * w for t, w in antp]
    pts += [a + d * (t * L) - an * w for t, w in reversed(postp)]
    return smooth(pts)


UA_A = [(-0.06, 4.5), (0.08, 6.3), (0.3, 5.0), (0.58, 5.1), (0.85, 4.0), (1.0, 3.6), (1.1, 2.2)]
UA_P = [(-0.06, 4.5), (0.1, 6.6), (0.38, 5.4), (0.7, 4.5), (1.0, 3.9), (1.1, 2.2)]
FA_A = [(-0.08, 3.4), (0.06, 4.3), (0.3, 4.4), (0.7, 3.1), (1.0, 2.5), (1.08, 1.8)]
FA_P = [(-0.08, 3.4), (0.06, 4.3), (0.25, 4.6), (0.62, 3.2), (1.0, 2.5), (1.08, 1.8)]
TH_A = [(-0.1, 6.0), (0.05, 8.6), (0.4, 8.2), (0.75, 6.6), (0.95, 5.6), (1.07, 3.6)]
TH_P = [(-0.1, 6.0), (0.05, 9.4), (0.42, 7.6), (0.8, 5.8), (1.0, 5.2), (1.07, 3.6)]
SH_A = [(-0.06, 4.4), (0.06, 5.4), (0.3, 4.5), (0.7, 3.3), (0.97, 2.9), (1.06, 2.2)]
SH_P = [(-0.06, 4.4), (0.06, 5.0), (0.27, 6.3), (0.52, 4.8), (0.82, 3.0), (0.97, 2.9), (1.06, 2.2)]


def torso_path(S, H):
    u = (S - H).n()
    fr = V(-u.y, u.x)
    T = (S - H).len() / 39
    P = lambda a, b: H + u * (a * T) + fr * b
    pts = [P(47, 4.8), P(42, 8.8), P(35, 13.6), P(28, 14.0), P(22, 11.9), P(14, 11.0), P(6, 11.0), P(0, 9.6), P(-6, 6.2),
           P(-10, -1), P(-9, -9), P(-2, -12.6), P(7, -10.6), P(15, -10.4), P(24, -12.0), P(33, -12.6), P(41, -9.6), P(47, -4.4)]
    return smooth(pts)


# ---------- cuerpo ----------

def ant(a, b):
    return (b - a).n().perp() * -1


def arm_shapes(S, E, W):
    d = (W - E).n()
    sh = [outline(S, E, UA_A, UA_P), circ(E, 3.9), outline(E, W, FA_A, FA_P)]
    hand = [circ(W + d * 3.4, 3.6), cap(W, 2.7, W + d * 5.4, 3.1)]
    return sh, hand


def leg_shapes(H, K, A, heel, toe):
    th = [outline(H, K, TH_A, TH_P)]
    sh = [outline(K, A, SH_A, SH_P), circ(K, 5.4)]
    ball = lerp(heel, toe, 0.68)
    up = (A - lerp(heel, toe, 0.4))
    ft = [cap(A, 3.3, ball, 2.5), cap(heel, 2.9, toe, 1.7), circ(heel, 3.0)]
    return th, sh, ft


def torso_shapes(S, H, hoff=2.0):
    u = (S - H).n()
    fr = V(-u.y, u.x)
    hc = S + u * 20 + fr * hoff
    t = [
        torso_path(S, H),
        cap(S + u * 6 - fr * 1.5, 5.8, S + u * 13 + fr * 1.0, 4.8),
    ]
    head = [
        ell(hc, 7.4, 8.6, (fr).ang()),
        cap(hc - u * 2.5 + fr * 2.5, 5.4, hc - u * 6.6 + fr * 5.6, 2.6),
        circ(hc + fr * 7.2 - u * 0.2, 1.5),
    ]
    return t, head, u, fr, hc


class Fig:
    def __init__(s, pid):
        s.pid = pid
        s.defs = []
        s.n = 0

    def clip(s, shapes, overlays):
        s.n += 1
        cid = f"{s.pid}c{s.n}"
        s.defs.append(f'<clipPath id="{cid}">{"".join(shapes)}</clipPath>')
        return f'<g clip-path="url(#{cid})">{"".join(overlays)}</g>'


def person(F, J, hi, hoff=2.0, front_extra="", mid_extra=""):
    """Devuelve (lejano, cercano). J: articulaciones; hi: músculos destacados."""
    far, near = [], []
    # extremidades lejanas
    for side, cls_b, cls_m in (("f", "bf", "mf"), ):
        Sf, Ef, Wf = J["Sf"], J["Ef"], J["Wf"]
        Hf, Kf, Af = J["Hf"], J["Kf"], J["Af"]
        th, sh, ft = leg_shapes(Hf, Kf, Af, J["heelf"], J["toef"])
        far.append(f'<g class="{cls_b}">{"".join(th + sh + ft)}</g>')
        far.append(leg_overlays(F, Hf, Kf, Af, th, sh, hi, cls_m))
        arm, hand = arm_shapes(Sf, Ef, Wf)
        far.append(f'<g class="{cls_b}">{"".join(arm + hand)}</g>')
        far.append(arm_overlays(F, Sf, Ef, Wf, arm, hi, cls_m))
    S, H, E, W, K, A = J["S"], J["H"], J["E"], J["W"], J["K"], J["A"]
    t, head, u, fr, hc = torso_shapes(S, H, hoff)
    near.append(f'<g class="b">{"".join(t + head)}</g>')
    ov = []
    if "chest" in hi:
        ov.append(ell(S - u * 8 + fr * 9.5, 7.8, 8.6, fr.ang(), "m"))
    if "lats" in hi:
        ov.append(ell(lerp(S, H, 0.36) - fr * 6.5, 6.5, 15, fr.ang(), "m"))
    if "glutes" in hi:
        ov.append(ell(H - fr * 7 - u * 0.5, 8.5, 9.5, fr.ang(), "m"))
    if ov:
        near.append(F.clip(t, ov))
    # pierna cercana
    th, sh, ft = leg_shapes(H, K, A, J["heel"], J["toe"])
    near.append(f'<g class="halo">{"".join(th + sh + ft)}</g><g class="b">{"".join(th + sh + ft)}</g>')
    near.append(leg_overlays(F, H, K, A, th, sh, hi, "m"))
    near.append(mid_extra)
    arm, hand = arm_shapes(S, E, W)
    near.append(f'<g class="halo">{"".join(arm + hand)}</g><g class="b">{"".join(arm + hand)}</g>')
    near.append(F.clip(arm[:1], [ell(lerp(S, E, 0.1), 6.0, 7.0, (E - S).ang(), "t")]))
    near.append(arm_overlays(F, S, E, W, arm, hi, "m"))
    # líneas de definición
    upper = arm[:1]
    pass
    if "chest" not in hi:
        near.insert(1, F.clip(t, [ell(S - u * 8 + fr * 9.5, 7.8, 8.6, fr.ang(), "t")]))
    if "quads" not in hi:
        near.append(F.clip(th, [ell(lerp(H, K, 0.5) + ant(H, K) * 6.2, (K - H).len() * 0.56, 7.4, (K - H).ang(), "t")]))
    near.append(F.clip(sh, [ell(lerp(K, A, 0.32) - ant(K, A) * 4, (A - K).len() * 0.3, 4.5, (A - K).ang(), "t")]))
    near.append(front_extra)
    return "".join(far), "".join(near)


def defs_lines(S, H, E, W, K, A, u, fr):
    out = []
    # pliegue de la cadera y del pecho
    p1 = H + fr * 7 + u * 4
    p2 = H + fr * 3 - u * 2
    out.append(f'<path class="dl" d="M{f(p1.x)} {f(p1.y)}Q{f((H + fr * 6).x)} {f((H + fr * 6).y)} {f(p2.x)} {f(p2.y)}"/>')
    return "".join(out)


def leg_overlays(F, H, K, A, th, sh, hi, cls):
    out = []
    an1, an2 = ant(H, K), ant(K, A)
    if "quads" in hi:
        out.append(F.clip(th, [ell(lerp(H, K, 0.5) + an1 * 6.2, (K - H).len() * 0.56, 7.4, (K - H).ang(), cls)]))
    if "hams" in hi:
        out.append(F.clip(th, [ell(lerp(H, K, 0.5) - an1 * 6, (K - H).len() * 0.5, 6.5, (K - H).ang(), cls)]))
    if "calves" in hi:
        out.append(F.clip(sh, [ell(lerp(K, A, 0.32) - an2 * 4, (A - K).len() * 0.3, 4.5, (A - K).ang(), cls)]))
    return "".join(out)


def arm_overlays(F, S, E, W, arm, hi, cls):
    out = []
    an1 = ant(S, E)
    upper = arm[:1]
    if "delt_front" in hi:
        out.append(F.clip(upper, [ell(lerp(S, E, 0.08) + an1 * 4.5, 5.5, 6.5, (E - S).ang(), cls)]))
    if "delt_rear" in hi:
        out.append(F.clip(upper, [ell(lerp(S, E, 0.08) - an1 * 4.5, 5.5, 6.5, (E - S).ang(), cls)]))
    if "biceps" in hi:
        out.append(F.clip(upper, [ell(lerp(S, E, 0.58) + an1 * 4.2, (E - S).len() * 0.36, 4.4, (E - S).ang(), cls)]))
    if "triceps" in hi:
        out.append(F.clip(upper, [ell(lerp(S, E, 0.52) - an1 * 4.2, (E - S).len() * 0.42, 4.6, (E - S).ang(), cls)]))
    return "".join(out)


def svg(F, body, caption):
    return (f'<figure><svg viewBox="0 0 200 160" role="img" aria-label="{caption}">'
            f'<defs>{"".join(F.defs)}</defs>{body}</svg><figcaption>{caption}</figcaption></figure>')


FLOOR = 146


def floor():
    return f'<line class="fl" x1="12" y1="{FLOOR}" x2="188" y2="{FLOOR}"/>'


# ---------- 1. press banca ----------

def bench():
    F = Fig("pb")
    S, H = V(66, 99), V(104, 100)
    W = V(67, 57)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    A = V(140, 139)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.y < b.y else b)
    Sf, Wf = V(63, 98), V(63, 56)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    Hf, Af = V(102, 99), V(131, 139)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.y < b.y else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=V(137, 142.6), toe=V(156, 143.6),
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=V(128, 142.6), toef=V(147, 143.6))
    bar = V(67.5, 53.5)
    back = [
        # rack
        rrect(30, 36, 6, FLOOR - 36, 2, "mk"),
        rrect(30, 49, 14, 4, 2, "mk"),
        rrect(22, FLOOR - 4, 22, 4, 2, "mk"),
        # disco
        circ(bar, 19, "pl"), circ(bar, 13.5, "pl2"), circ(bar, 4.2, "mk"),
        # banco
        rrect(46, 118, 6, FLOOR - 118, 2, "mk"),
        rrect(112, 118, 6, FLOOR - 118, 2, "mk"),
        rrect(40, FLOOR - 4, 18, 4, 2, "mk"), rrect(106, FLOOR - 4, 18, 4, 2, "mk"),
        rrect(40, 116, 84, 4, 1.5, "sk"),
        rrect(26, 109, 98, 8, 4, "pad"),
    ]
    front = [circ(bar + V(0, 0.4), 2.4, "bar")]
    fa, nr = person(F, J, {"chest", "delt_front", "triceps"}, hoff=-1.5, front_extra="".join(front))
    return svg(F, floor() + "".join(back) + fa + nr, "Press banca")


# ---------- 2. jalón al pecho ----------

def pulldown():
    F = Fig("jp")
    H, S = V(84, 104), V(76, 66)
    W = V(91, 62)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.y > b.y else b)
    A = V(114, 139)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    Sf, Wf = V(74, 65), V(88, 61)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.y > b.y else b)
    Hf, Af = V(82, 103), V(107, 139)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=V(111, 142.6), toe=V(130, 143.6),
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=V(104, 142.6), toef=V(123, 143.6))
    d = (W - E).n()
    grip = W + d * 3.4
    pul = V(grip.x + 4.5, 17)
    back = [
        # columna y pila de pesas
        rrect(150, 12, 12, FLOOR - 12, 3, "mk"),
        rrect(138, 96, 14, 46, 2, "sk"),
        *[line(V(139, 100 + i * 6), V(151, 100 + i * 6), "sep", 1) for i in range(7)],
        rrect(136, FLOOR - 4, 34, 4, 2, "mk"),
        # brazo superior y polea
        rrect(pul.x - 2, 11, 162 - pul.x + 2, 6, 3, "mk"),
        line(V(pul.x - 4.5, 17), V(grip.x, grip.y), "cab", 1.1),
        circ(pul, 6, "pl"), circ(pul, 2, "mk"),
        # asiento
        rrect(82, 120, 6, FLOOR - 120, 2, "mk"),
        rrect(62, FLOOR - 4, 52, 4, 2, "mk"),
        rrect(62, 112, 46, 8, 4, "pad"),
        # soporte del rodillo
        line(V(119, 92), V(150, 92), "mkl", 4),
    ]
    roll = [circ(V(119, 92), 6.6, "pad"), circ(V(119, 92), 2, "mk")]
    # barra: extremo visto de lado con el puño
    barg = [circ(grip, 2.5, "bar"), line(grip, grip + V(-6, 6), "barl", 2.6)]
    fa, nr = person(F, J, {"lats", "biceps", "delt_rear"}, mid_extra="".join(roll), front_extra="".join([circ(grip, 2.3, "bar")]))
    return svg(F, floor() + "".join(back) + "".join(barg[1:2]) + fa + nr, "Jalón al pecho")


# ---------- 3. extensión de cuádriceps ----------

def legext():
    F = Fig("ec")
    H, S = V(82, 104), V(78, 66)
    W = V(94, 104)
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    K = V(114, 104)
    ang = math.radians(-12)
    A = K + V(math.cos(ang), math.sin(ang)) * L_SH
    Kf = V(111, 103)
    Af = Kf + V(math.cos(ang), math.sin(ang)) * L_SH
    dsh = (A - K).n()
    an = dsh.perp() * -1
    heel = A + dsh * 3.2 - an * 1.5
    toe = A + an * 12 + dsh * 5.5
    dshf = (Af - Kf).n()
    anf = dshf.perp() * -1
    Sf, Wf = V(76, 65), V(91, 103)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.x < b.x else b)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=heel, toe=toe,
             Sf=Sf, Hf=V(80, 103), Ef=Ef, Wf=Wf, Kf=Kf, Af=Af,
             heelf=Af + dshf * 3.2 - anf * 1.5, toef=Af + anf * 12 + dshf * 5.5)
    roller = lerp(K, A, 0.84) + an * 8.6
    piv = K + V(0, 2)
    back = [
        # pila de pesas
        rrect(16, 26, 12, FLOOR - 26, 3, "mk"),
        rrect(28, 96, 14, 46, 2, "sk"),
        *[line(V(29, 100 + i * 6), V(41, 100 + i * 6), "sep", 1) for i in range(7)],
        rrect(12, FLOOR - 4, 40, 4, 2, "mk"),
        # respaldo
        poly([V(59, 50), V(66, 49), V(69, 109), V(62, 109)], "pad", ' stroke-linejoin="round" stroke-width="5"'),
        line(V(60, 112), V(28, 60), "mkl", 4),
        # asiento y estructura
        rrect(86, 122, 6, FLOOR - 122, 2, "mk"),
        rrect(64, FLOOR - 4, 60, 4, 2, "mk"),
        rrect(60, 112, 54, 9, 4.5, "pad"),
        line(piv, piv + V(0, 18), "mkl", 4),
    ]
    mid = []
    front = [line(piv, roller, "mkl", 3.4), circ(roller, 5.8, "pad"), circ(roller, 2, "mk"), circ(piv, 4, "pl"), circ(piv, 1.6, "mk"),
             ]
    grip = W + (W - E).n() * 3.4
    back.append(line(grip, V(grip.x, 120), "mkl", 3.5))
    fa, nr = person(F, J, {"quads"}, front_extra="".join(front))
    return svg(F, floor() + "".join(back) + fa + "".join(mid) + nr, "Extensión de cuádriceps")


# ---------- 4. sentadilla hack ----------

def hack():
    F = Fig("sh")
    A = V(127, 129)
    H = V(110, 107)
    K = ik(H, A, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    u = V(-1, -1).n()
    fr = V(-u.y, u.x)
    bk = fr * -1
    S = H + u * 39
    Wg = S + u * 1 + fr * 12
    W = Wg
    E = ik(S, W, L_UA, L_FA, lambda a, b: a if a.y > b.y else b)
    Af = V(121, 129)
    Hf = H + V(-2, -1)
    Kf = ik(Hf, Af, L_TH, L_SH, lambda a, b: a if a.x > b.x else b)
    Sf = S + V(-2, -1)
    Wf = W + V(-2, -1)
    Ef = ik(Sf, Wf, L_UA, L_FA, lambda a, b: a if a.y > b.y else b)
    # plataforma inclinada
    p0, p1 = V(104, 137.5), V(158, 129)
    pd = (p1 - p0).n()
    pn = pd.perp()
    def on_plat(x, r):
        t = (x - p0.x) / pd.x
        return p0 + pd * t - pn * (-r) if False else p0 + pd * t + V(0, -r)
    heel = on_plat(122, 3.1)
    toe = on_plat(143, 1.9)
    heelf = on_plat(116, 3.1)
    toef = on_plat(137, 1.9)
    J = dict(S=S, H=H, E=E, W=W, K=K, A=A, heel=heel, toe=toe,
             Sf=Sf, Hf=Hf, Ef=Ef, Wf=Wf, Kf=Kf, Af=Af, heelf=heelf, toef=toef)
    # riel
    R0 = H + bk * 25
    rb = R0 - u * ((FLOOR - 4 - R0.y) / (-u.y))
    rt = R0 + u * 70
    pad_a = H + bk * 11.5 - u * 8
    pad_b = S + bk * 11.5 + u * 10
    pad = [pad_a, pad_b, pad_b + bk * 6, pad_a + bk * 6]
    plate = S + bk * 24 + u * 2
    sp = S + u * 7 + fr * 0.5
    back = [
        line(rb, rt, "mkl", 5),
        line(rt, V(rt.x, FLOOR - 2), "mkl", 5),
        rrect(rt.x - 10, FLOOR - 4, 112, 4, 2, "mk"),
        circ(plate, 16, "pl"), circ(plate, 11, "pl2"), circ(plate, 3.5, "mk"),
        line(lerp(pad_a, pad_b, 0.15) + bk * 6, lerp(pad_a, pad_b, 0.15) + bk * 12, "mkl", 4),
        line(lerp(pad_a, pad_b, 0.85) + bk * 6, lerp(pad_a, pad_b, 0.85) + bk * 12, "mkl", 4),
        line(lerp(pad_a, pad_b, 0.1) + bk * 12, lerp(pad_a, pad_b, 0.9) + bk * 12, "mkl", 4),
        poly(pad, "pad", ' stroke-linejoin="round" stroke-width="5"'),
        # plataforma
        poly([p0, p1, p1 + V(0, 5), p0 + V(0, 5)], "pad", ' stroke-linejoin="round" stroke-width="3"'),
        line(lerp(p0, p1, 0.5) + V(0, 6), V(lerp(p0, p1, 0.5).x, FLOOR - 2), "mkl", 5),
    ]
    spad = [ell(sp, 7, 3.6, fr.ang(), "pad"),
            line(sp, W + (W - E).n() * 3.4, "mkl", 3)]
    fa, nr = person(F, J, {"quads", "glutes"}, front_extra="".join(spad[:1]))
    return svg(F, floor() + "".join(back) + fa + spad[1] + nr, "Sentadilla hack")


CSS = """
:root{--ink:#1D1B18;--muted:#6B645A;--line:#E4DDD1;--line-strong:#CFC6B7;--sunken:#EEE8DE;--surface:#FFFDF9;--act:#4A55C9}
body{margin:0;padding:24px;background:var(--surface);font-family:system-ui,sans-serif;color:var(--ink)}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
figure{margin:0}svg{width:100%;height:auto;display:block;background:transparent}
figcaption{font-size:13px;color:var(--muted);text-align:center;margin-top:4px}
svg .b{fill:color-mix(in srgb,var(--ink) 64%,var(--surface))}
svg .bf{fill:color-mix(in srgb,var(--ink) 30%,var(--surface))}
svg .m{fill:var(--act)}
svg .mf{fill:color-mix(in srgb,var(--act) 48%,var(--surface))}
svg .mk{fill:var(--line-strong)}
svg .sk{fill:var(--sunken);stroke:var(--line-strong);stroke-width:1}
svg .pad{fill:var(--line-strong);stroke:var(--line-strong)}
svg .pl{fill:var(--sunken);stroke:var(--line-strong);stroke-width:2}
svg .pl2{fill:none;stroke:var(--line-strong);stroke-width:1}
svg .mkl{stroke:var(--line-strong);fill:none}
svg .sep{stroke:var(--line-strong)}
svg .cab{stroke:var(--muted)}
svg .bar{fill:var(--muted)}
svg .barl{stroke:var(--muted)}
svg .fl{stroke:var(--line);stroke-width:1.5}
svg .t{fill:color-mix(in srgb,var(--ink) 54%,var(--surface))}
svg .halo{fill:var(--surface);stroke:var(--surface);stroke-width:1.5;stroke-linejoin:round}
svg .dl{fill:none;stroke:var(--surface);stroke-width:.8;opacity:.45}
"""


def main():
    figs = [bench(), pulldown(), legext(), hack()]
    html = (f'<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Silueta</title>'
            f'<meta name="viewport" content="width=device-width,initial-scale=1"><style>{CSS}</style></head>'
            f'<body><div class="grid">{"".join(figs)}</div></body></html>')
    open(OUT, "w", encoding="utf-8").write(html)




if __name__ == "__main__":
    main()
