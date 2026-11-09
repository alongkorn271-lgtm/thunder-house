"""KK01 ST07 โครงหลังคาเหล็ก – exec'd after kk01_walls.py (kk01_load.py). Steel to the real profile (th_steel.py).

Drawings: A-10/A-11 sections (pitch 30°, wall plate top +4.30, ridges +6.28 main / +5.87 left wing / +5.44 right wing),
S-05 (wall plates + ties 2[]125×50×20×2.3, king posts 2[]125), S-06 (rafter supports 2[]125 for the lean-to and the
front canopy, top +3.30), S-07 (lean-to / canopy: rafters C100×50×20×2.3 @1.00, purlins C75×45×15×2.3 @1.00),
S-08 (main roof: rafters C100×50×20×2.3 @1.00, battens galvanised 1"×1" @0.33–0.34).

Main roof = the union of three hip roofs on the plate rectangles (HIP_BOXES): height = max over boxes of the box's
own hip field (min of its 4 planes). Every plane rises 30° inward from its plate line; the rafter underside passes
through the plate's outer top edge (practice); eave 1.00 m from the plate line to the fascia's outer face (S-05).
Rafters, battens, hips, ridges and valleys all come from sampling that field, so jack rafters, the two valleys and the
hidden wing hips fall out by themselves. Members butt square against the 2C they meet (cut back by half widths).
Objects: one per member, named RF_<kind>_<n>, data props kind / section / p0 / p1 / axis. Spec: ST07_roof_spec.md.
"""
from mathutils import Vector

_ss = open(_os.path.join(KK01_DIR, "th_steel.py"), encoding="utf-8").read()
if "th_steel" in bpy.data.texts:
    bpy.data.texts["th_steel"].from_string(_ss)
else:
    bpy.data.texts.new("th_steel").from_string(_ss)
exec(compile(_ss, "th_steel", "exec"))

PITCH = 30.0
PLATE_TOP = 4.30                                   # A-10 ระดับหัวเสา = top of the wall plate
EAVE = 1.00                                        # plate line → fascia outer face (S-05 roof outline)
FASCIA_T = 0.022                                   # เชิงชาย 2in1 23.5 × 2.2 cm (A-10): rafters stop at its back
HIP_BOXES = {"M": (0.0, 1.0, 13.0, 7.5), "L": (0.0, 0.0, 5.0, 6.0), "R": (9.5, 0.0, 13.0, 4.5)}   # plate rects
SECTIONS = {   # name: (kind, dims m) — C: lipped channel h b lip t; 2C: two C toe to toe; BOX: square tube B H t
    "2C125": ("2C", (0.125, 0.050, 0.020, 0.0023)), "C100": ("C", (0.100, 0.050, 0.020, 0.0023)),
    "C75": ("C", (0.075, 0.045, 0.015, 0.0023)), "BOX25": ("BOX", (0.025, 0.025, 0.0012))}
ROOF = dict(rafter="C100", rafter_s=1.00, batten="BOX25", batten_first=0.34, batten_top=0.04, batten_max=0.34,
            member="2C125", min_piece=0.20, stock=6.0)
PLATES = [   # wall plates (S-05 "อะเส"), then ties (ขื่อ), all 2[]125 at the same level; earlier runs through
    ((0.0, 7.5), (13.0, 7.5)), ((0.0, 0.0), (0.0, 7.5)), ((13.0, 0.0), (13.0, 7.5)), ((0.0, 0.0), (5.0, 0.0)),
    ((9.5, 0.0), (13.0, 0.0)), ((5.0, 0.0), (5.0, 7.5)), ((9.5, 0.0), (9.5, 7.5)), ((5.0, 1.0), (9.5, 1.0)),
    ((0.0, 4.25), (13.0, 4.25)), ((0.0, 3.5), (5.0, 3.5)), ((2.5, 0.0), (2.5, 7.5)), ((9.5, 3.0), (13.0, 3.0)),
    ((11.25, 0.0), (11.25, 3.0))]
KING_POSTS = [(3.25, 4.25), (5.0, 4.25), (7.25, 4.25), (9.75, 4.25), (2.5, 2.5), (2.5, 3.5), (11.25, 1.75), (11.25, 2.75)]
LEAN = dict(top=3.30, support="2C125", rafter="C100", purlin="C75", s=1.00)
LEAN_ROOFS = {   # x0, x1, y0, y1 of the sheet frame; support lines (axis-0 runs at y, from x0 to x1)
    "lean-to": dict(x=(2.5, 10.5), y=(8.2, 13.2), supports=[(9.2, 2.5, 10.5), (12.2, 2.5, 10.5)]),
    "canopy": dict(x=(5.115, 9.385), y=(-1.0, 0.885), supports=[(0.0, 5.115, 9.385), (0.835, 5.115, 9.385)])}   # between the
    # plastered faces of columns G3 / G5 and against the plastered y 1.0 wall (S-06 draws it from grid 3 to 5)
C_ROOF = "KK01 ST07 Roof frame"
STAGES.append(C_ROOF)


def _tan():
    return math.tan(math.radians(PITCH))


def _sec(name):
    kind, d = SECTIONS[name]
    if kind == "BOX":
        return d[0], d[1]                                  # width, depth
    return (2 * d[1] if kind == "2C" else d[1]), d[0]


def _sec_area(name):
    kind, d = SECTIONS[name]
    if kind == "BOX":
        o, i = box_tube(*d)
        return tube_area(o, i)
    a = area(lipped_c(*d))
    return 2 * a if kind == "2C" else a


def _member(bm, name, p0, p1, up_hint):
    """Sweep section `name` from p0 to p1 (bottom-centre line); `up` = up_hint made perpendicular to the axis."""
    kind, d = SECTIONS[name]
    p0, p1 = Vector(p0), Vector(p1)
    ax = (p1 - p0)
    L = ax.length
    ax.normalize()
    up = (Vector(up_hint) - ax * Vector(up_hint).dot(ax)).normalized()
    side = ax.cross(up)
    if kind == "BOX":
        o, i = box_tube(*d)
        tube(bm, o, i, 0.0, L, lambda u, s, z: tuple(p0 + ax * u + side * s + up * z))
    elif kind == "C":
        poly = lipped_c(*d)
        prism(bm, poly, 0.0, L, lambda u, s, z: tuple(p0 + ax * u + side * (s - d[1] / 2) + up * z))
    else:   # 2C toe to toe: webs at ±b, toes meeting on the centre line
        poly = lipped_c(*d)
        prism(bm, poly, 0.0, L, lambda u, s, z: tuple(p0 + ax * u + side * (s - d[1]) + up * z))
        prism(bm, poly, 0.0, L, lambda u, s, z: tuple(p0 + ax * u + side * (d[1] - s) + up * z))
    return L


# ---------------------------------------------------------------- the roof field

def _planes():
    """Global planes (ax, k, dr): rising inward along axis ax from the plate line at k, dr = ±1; coplanar box sides
    are one plane."""
    out = []
    for x0, y0, x1, y1 in HIP_BOXES.values():
        for p in ((0, x0, 1), (0, x1, -1), (1, y0, 1), (1, y1, -1)):
            if p not in out:
                out.append(p)
    return out


def _box_planes(b):
    x0, y0, x1, y1 = b
    return [(0, x0, 1), (0, x1, -1), (1, y0, 1), (1, y1, -1)]


def _d(p, x, y):
    ax, k, dr = p
    return dr * ((x, y)[ax] - k)


def _roof_d(x, y):
    """Inward distance of the roof surface at (x, y): max over boxes whose eave rect holds the point of the box's min
    plane distance; None outside every eave."""
    best = None
    for b in HIP_BOXES.values():
        if b[0] - EAVE - 1e-9 <= x <= b[2] + EAVE + 1e-9 and b[1] - EAVE - 1e-9 <= y <= b[3] + EAVE + 1e-9:
            m = min(_d(p, x, y) for p in _box_planes(b))
            best = m if best is None else max(best, m)
    return best


def _on(p, x, y, eps=1e-7):
    r = _roof_d(x, y)
    return r is not None and abs(_d(p, x, y) - r) < eps and any(
        p in _box_planes(b) and b[0] - EAVE - 1e-9 <= x <= b[2] + EAVE + 1e-9 and b[1] - EAVE - 1e-9 <= y <= b[3] + EAVE + 1e-9
        and abs(min(_d(q, x, y) for q in _box_planes(b)) - r) < eps and abs(_d(p, x, y) - r) < eps for b in HIP_BOXES.values())


def _z_under(dist):
    """Rafter underside at inward distance dist (through the plate's outer top edge)."""
    return PLATE_TOP + (dist + _sec(ROOF["member"])[0] / 2) * _tan()


def _z_top(dist):
    return _z_under(dist) + _sec(ROOF["rafter"])[1] / math.cos(math.radians(PITCH))


def _xy(p, u, v):
    return (u, v) if p[0] == 0 else (v, u)


def _intervals(f, a, b, step=0.01):
    """Sub-intervals of [a, b] where f is true, ends refined by bisection."""
    n = max(2, int(math.ceil((b - a) / step)))
    ts = [a + (b - a) * i / n for i in range(n + 1)]
    vals = [f(t) for t in ts]
    out, start = [], None

    def edge(lo, hi, want_lo):
        for _ in range(40):
            m = (lo + hi) / 2
            if f(m) == want_lo:
                lo = m
            else:
                hi = m
        return (lo + hi) / 2
    for i, v in enumerate(vals):
        if v and start is None:
            start = a if i == 0 else edge(ts[i - 1], ts[i], False)
        if not v and start is not None:
            out.append((start, edge(ts[i - 1], ts[i], True)))
            start = None
    if start is not None:
        out.append((start, b))
    return out


def _takeover(p, x, y):
    """The plane that takes the roof over just past (x, y): 'ridge' (parallel), 'cross' (hip / valley) or None (eave)."""
    r = _roof_d(x, y)
    if r is None:
        return None
    others = [q for q in _planes() if q != p and abs(_d(q, x, y) - r) < 1e-4]
    if any(q[0] == p[0] for q in others):
        return "ridge"
    return "cross" if others else None


def _cut_back(kind, own_w):
    """How far a member running into a 2C stops short of that 2C's centreline (square-cut end, no overlap)."""
    hw = _sec(ROOF["member"])[0] / 2
    if kind == "ridge":
        return hw
    s45 = math.sin(math.radians(45))
    return hw / s45 + own_w / 2


def _plane_extent(p):
    """v range of the plane's eave line (union of the owning boxes' eave rects)."""
    v = [((b[1], b[3]) if p[0] == 0 else (b[0], b[2])) for b in HIP_BOXES.values() if p in _box_planes(b)]
    return min(a for a, _ in v) - EAVE, max(c for _, c in v) + EAVE


def _plane_top_d(p):
    return max(min(b[2] - b[0], b[3] - b[1]) / 2 for b in HIP_BOXES.values() if p in _box_planes(b))


def _clear_ok(p, x, y, ridge_ok=False):
    """(x, y) may hold part of a member of plane p: on p, past the eave, or (battens, whose width runs up the
    slope) across a ridge on the parallel plane."""
    r = _roof_d(x, y)
    if r is None or _on(p, x, y):
        return True
    return ridge_ok and any(q[0] == p[0] and q != p and _on(q, x, y) for q in _planes())


def _lat():
    """Plan clearance across a member that must stay clear of a 45° 2C (hip / valley): its half width / sin 45°."""
    return _sec(ROOF["member"])[0] / 2 / math.sin(math.radians(45)) + 0.005    # + 5 mm fitting gap


def _eave_start():
    """Inward distance where a rafter's underside starts: its square-cut end leans h·sin θ downslope at the top, so
    the bottom starts that far in from the fascia back and the top corner just meets the board."""
    return -(EAVE - FASCIA_T) + _sec(ROOF["rafter"])[1] * math.sin(math.radians(PITCH))


def _rafter_pieces():
    """[(plane, v, d0, d1)] rafter pieces (inward distances along the plane), ≥ min_piece long in plan. Both flange
    edges keep clear of hips / valleys; a rafter stops 1/2 the ridge width short of the ridge line; a piece that starts
    at a valley starts a further h·sin θ up (its square-cut end leans downslope at the top)."""
    out, w, h = [], _sec(ROOF["rafter"])[0], _sec(ROOF["rafter"])[1]
    e = -(EAVE - FASCIA_T)
    for p in _planes():
        ax, k, dr = p
        lo, hi = _plane_extent(p)
        vs = _even(lo + 0.03, hi - 0.03, ROOF["rafter_s"])
        top = _plane_top_d(p) + 0.2
        off = w / 2 + _lat()
        for v in vs:
            f = lambda dd, v=v: _on(p, *_xy(p, k + dr * dd, v)) and all(
                _clear_ok(p, *_xy(p, k + dr * dd, v + o)) for o in (-off, off))
            for a, b in _intervals(f, e, top):
                if a > e + 1e-6:
                    a += h * math.sin(math.radians(PITCH))
                else:
                    a = _eave_start()
                if _takeover(p, *_xy(p, k + dr * (b + 1e-3), v)) == "ridge":
                    b -= _cut_back("ridge", w)
                if b - a >= ROOF["min_piece"]:
                    out.append((p, v, a, b))
    return out


def _batten_courses(p):
    """Slope distances s from the eave line (fascia outer face) of the batten courses (CPAC: first 0.34, top 0.04
    under the ridge line, between evenly ≤ batten_max)."""
    c = math.cos(math.radians(PITCH))
    s_top = (_plane_top_d(p) + EAVE) / c - ROOF["batten_top"]
    s1 = ROOF["batten_first"]
    n = math.ceil((s_top - s1) / ROOF["batten_max"] - 1e-9)
    return [s1 + i * (s_top - s1) / n for i in range(n + 1)]


def _batten_pieces():
    out, (w, hb) = [], _sec(ROOF["batten"])
    c = math.cos(math.radians(PITCH))
    for p in _planes():
        ax, k, dr = p
        lo, hi = _plane_extent(p)
        off = w / 2 * c + hb * math.sin(math.radians(PITCH)) + _lat()   # the batten tilts with the slope
        for s in _batten_courses(p):
            dd = -EAVE + s * c
            f = lambda v, dd=dd: _on(p, *_xy(p, k + dr * dd, v)) and all(
                _clear_ok(p, *_xy(p, k + dr * (dd + o), v), True) for o in (-off, off))
            for a, b in _intervals(f, lo, hi, 0.01):
                if b - a >= ROOF["min_piece"]:
                    out.append((p, s, dd, a, b))
    return out


def _lines():
    """Hips, valleys, ridges: [(kind, (x0, y0), (x1, y1), planes)] where two planes really meet on the roof: just to
    one side the roof is the one plane, just to the other side the other (a coplanar seam is not a line)."""
    pl, out = _planes(), []
    for p, q in itertools.combinations(pl, 2):
        if p[0] == q[0]:
            if p[2] == q[2]:
                continue
            m = (p[1] + q[1]) / 2
            pt = lambda v, p=p, m=m: _xy(p, m, v)
            side = lambda P, sg, p=p: (P[0] + sg * 0.002, P[1]) if p[0] == 0 else (P[0], P[1] + sg * 0.002)
            lo, hi = -EAVE - 1, 14 + EAVE
        else:
            px, py = (p, q) if p[0] == 0 else (q, p)
            pt = lambda x, px=px, py=py: (x, py[1] + py[2] * px[2] * (x - px[1]))
            g = Vector((1, -py[2] * px[2])).normalized() * 0.002
            side = lambda P, sg, g=g: (P[0] + sg * g.x, P[1] + sg * g.y)
            lo, hi = -EAVE - 0.5, 13 + EAVE + 0.5
        on2 = lambda v, p=p, q=q, pt=pt: _on(p, *pt(v), 1e-6) and _on(q, *pt(v), 1e-6)
        def real(v, p=p, q=q, pt=pt, side=side):     # one plane on one side, the other on the other side
            M = pt(v)
            s1, s2 = side(M, 1), side(M, -1)
            sides = [[r for r in (p, q) if _on(r, *S, 1e-6) and not _on(q if r == p else p, *S, 1e-6)] for S in (s1, s2)]
            return bool(sides[0] and sides[1] and sides[0] != sides[1])
        for a0, b0 in _intervals(on2, lo, hi, 0.005):
            for a, b in _intervals(lambda v: on2(v) and real(v), a0, b0, 0.005):   # a seam can turn into a line
                if b - a < 0.05:
                    continue
                a = a0 if a - a0 < 0.03 else a       # the side probe fails within its own reach of a junction
                b = b0 if b0 - b < 0.03 else b
                M = pt((a + b) / 2)
                s1 = side(M, 1)
                if p[0] == q[0]:
                    kind = "ridge"
                else:
                    r1 = p if _on(p, *s1, 1e-6) else q
                    other = q if r1 == p else p
                    kind = "hip" if _d(other, *s1) > _roof_d(*s1) + 1e-9 else "valley"
                out.append((kind, pt(a), pt(b), (p, q)))
    return out


def _line_z_top(kind, p0, p1, planes):
    """Top of a 2C member along a plan line: top corners on the planes (hip / ridge) or the line itself (valley)."""
    dd = _d(planes[0], *p0), _d(planes[0], *p1)
    hw = _sec(ROOF["member"])[0] / 2
    t = _tan()
    if kind == "ridge":
        return [_z_top(v) - hw * t for v in dd]
    if kind == "hip":
        return [_z_top(v) - hw * t / math.sqrt(2) for v in dd]
    return [_z_top(v) for v in dd]


def _roof_layout():
    """Everything of the frame as [(kind, section, p0, p1, up)] bottom-centre lines."""
    t, c = _tan(), math.cos(math.radians(PITCH))
    m_w, m_h = _sec(ROOF["member"])
    items = []
    # wall plates and ties, top at PLATE_TOP; later lines stop at the faces of earlier ones
    placed = []
    for (x0, y0), (x1, y1) in PLATES:
        ax = 0 if y0 == y1 else 1
        a, b = sorted(((x0, y0)[ax], (x1, y1)[ax]))
        k = (y0, x0)[ax]
        box = (*_xy_ax(ax, a - m_w / 2, k - m_w / 2), PLATE_TOP - m_h, *_xy_ax(ax, b + m_w / 2, k + m_w / 2), PLATE_TOP)
        box = (min(box[0], box[3]), min(box[1], box[4]), box[2], max(box[0], box[3]), max(box[1], box[4]), box[5])
        for q in _cut(box, placed):
            u0, u1 = q[ax], q[ax + 3]
            if u1 - u0 < 0.02:
                continue
            p0 = _xyz_ax(ax, u0, k, PLATE_TOP - m_h)
            p1 = _xyz_ax(ax, u1, k, PLATE_TOP - m_h)
            items.append(("plate", ROOF["member"], p0, p1, (0, 0, 1)))
            placed.append(q)
    plate_boxes = list(placed)
    # ridges, hips, valleys
    lines = _lines()
    nodes = {}
    for kind, a, b, planes in lines:
        for pnt in (a, b):
            key = (round(pnt[0], 3), round(pnt[1], 3))
            nodes.setdefault(key, []).append(kind)
    for kind, a, b, planes in sorted(lines, key=lambda l: ("ridge", "hip", "valley").index(l[0])):
        za, zb = _line_z_top(kind, a, b, planes)
        A, B = Vector((*a, za)), Vector((*b, zb))
        if kind != "ridge":   # back off at a node where a ridge (or another line) is: square-cut, no overlap
            for end in (0, 1):
                key = (round((a, b)[end][0], 3), round((a, b)[end][1], 3))
                if len(nodes.get(key, [])) > 1:
                    d = (B - A).normalized()
                    back = 0.16 if kind == "valley" else 0.10      # a valley comes in alongside the ridge
                    if end == 0:
                        A = A + d * back
                    else:
                        B = B - d * back
            # eave end: stop at the fascia backs (both eaves' plumb faces)
            target = -(EAVE - FASCIA_T)
            for end in (0, 1):
                P, Q = ((A, B), (B, A))[end]
                dP = _roof_d(P.x, P.y)
                if dP is not None and dP < target - 1e-9:
                    rate = (_roof_d(Q.x, Q.y) - dP) / (Q - P).xy.length       # inward distance per plan metre
                    move = (target - dP) / rate * (Q - P).length / (Q - P).xy.length
                    P2 = P + (Q - P).normalized() * move
                    dd_ = (Q - P).normalized()
                    P2 = P2 + dd_ * (m_h * abs(dd_.z) / max(dd_.xy.length, 1e-9))   # square cut: top meets the board
                    if kind == "hip":   # at an outside corner the hip's side corners face the two boards: half a width more
                        P2 = P2 + dd_ * (m_w / 2 / max(dd_.xy.length, 1e-9))
                    A, B = (P2, B) if end == 0 else (A, P2)
        d = B - A
        cphi = d.xy.length / d.length
        drop = m_h / cphi                                   # top line → bottom-centre line, vertically
        if kind in ("hip", "valley"):   # seat on the plates it crosses: raise until the bottom clears them (practice)
            side = Vector((-d.y, d.x, 0)).normalized() * (m_w / 2)
            lift = 0.0
            for S0 in (A - Vector((0, 0, drop)) + side, A - Vector((0, 0, drop)) - side):
                for q in plate_boxes:            # clip each bottom edge to the plate's plan rect: lowest at an end
                    t0, t1 = 0.0, 1.0
                    for c_, dc, lo_, hi_ in ((S0.x, d.x, q[0], q[3]), (S0.y, d.y, q[1], q[4])):
                        if abs(dc) < 1e-12:
                            if not lo_ <= c_ <= hi_:
                                t0, t1 = 1.0, 0.0
                            continue
                        a_, b_ = (lo_ - c_) / dc, (hi_ - c_) / dc
                        t0, t1 = max(t0, min(a_, b_)), min(t1, max(a_, b_))
                    if t0 <= t1:
                        zlow = min(S0.z + d.z * t0, S0.z + d.z * t1)
                        lift = max(lift, PLATE_TOP - zlow + 1e-4)
            B0 = A - Vector((0, 0, drop))
            dh = Vector((d.x, d.y, 0))
            for q in plate_boxes:                # a plate corner under the bottom face, between the two edges
                for cx, cy in ((q[0], q[1]), (q[3], q[1]), (q[0], q[4]), (q[3], q[4])):
                    rel = Vector((cx - B0.x, cy - B0.y, 0))
                    tt = rel.dot(dh) / dh.length_squared
                    perp = (rel - dh * tt).length
                    if 0 <= tt <= 1 and perp <= m_w / 2 + 1e-9:
                        lift = max(lift, PLATE_TOP - (B0.z + d.z * tt) + 1e-4)
            A, B = A + Vector((0, 0, lift)), B + Vector((0, 0, lift))
        items.append((kind, ROOF["member"], tuple(A - Vector((0, 0, drop))), tuple(B - Vector((0, 0, drop))), (0, 0, 1)))
    # king posts: tie top → ridge underside, 0.10 across the ridge
    ridges = [(a, b, *_line_z_top("ridge", a, b, pl)) for kind, a, b, pl in lines if kind == "ridge"]
    for x, y in KING_POSTS:
        r = [(a, b, za, zb) for a, b, za, zb in ridges if min(a[0], b[0]) - 1e-6 <= x <= max(a[0], b[0]) + 1e-6
             and min(a[1], b[1]) - 1e-6 <= y <= max(a[1], b[1]) + 1e-6]
        assert r, f"king post at ({x}, {y}) under no ridge"
        a, b, za, zb = r[0]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        hd = _sec(ROOF["member"])[1] / 2                    # a post at a ridge end steps in so the hips clear it
        for e, o_ in ((a, b), (b, a)):
            if math.hypot(x - e[0], y - e[1]) < hd + 1e-6:
                x, y = e[0] + (o_[0] - e[0]) / L * hd, e[1] + (o_[1] - e[1]) / L * hd
        f = math.hypot(x - a[0], y - a[1]) / L if L else 0
        ztop = za + (zb - za) * f - m_h
        along = (1, 0, 0) if abs(b[1] - a[1]) < 1e-9 else (0, 1, 0)
        items.append(("post", ROOF["member"], (x, y, PLATE_TOP), (x, y, ztop), along))
    # rafters
    w_r = _sec(ROOF["rafter"])[0]
    for p, v, d0, d1 in _rafter_pieces():
        ax, k, dr = p
        P0 = (*_xy(p, k + dr * d0, v), _z_under(d0))
        P1 = (*_xy(p, k + dr * d1, v), _z_under(d1))
        n = Vector(((-dr * math.sin(math.radians(PITCH))) if ax == 0 else 0, (-dr * math.sin(math.radians(PITCH))) if ax == 1 else 0,
                    math.cos(math.radians(PITCH))))
        items.append(("rafter", ROOF["rafter"], P0, P1, tuple(n)))
    # battens on the rafter tops
    for p, s, dd, a, b in _batten_pieces():
        ax, k, dr = p
        z = _z_top(dd)
        n = Vector(((-dr * math.sin(math.radians(PITCH))) if ax == 0 else 0, (-dr * math.sin(math.radians(PITCH))) if ax == 1 else 0,
                    math.cos(math.radians(PITCH))))
        P0 = (*_xy(p, k + dr * dd, a), z)
        P1 = (*_xy(p, k + dr * dd, b), z)
        items.append(("batten", ROOF["batten"], P0, P1, tuple(n)))
    # lean-to and canopy: supports (top LEAN top), rafters along y on them, purlins along x on the rafters
    sw, sh = _sec(LEAN["support"])
    rw, rh = _sec(LEAN["rafter"])
    for name, lr in LEAN_ROOFS.items():
        for y, x0, x1 in lr["supports"]:
            items.append(("support", LEAN["support"], (x0, y, LEAN["top"] - sh), (x1, y, LEAN["top"] - sh), (0, 0, 1)))
        xs = _even(lr["x"][0] + rw / 2, lr["x"][1] - rw / 2, LEAN["s"])
        for x in xs:
            items.append(("lean_rafter", LEAN["rafter"], (x, lr["y"][0], LEAN["top"]), (x, lr["y"][1], LEAN["top"]), (0, 0, 1)))
        pw, ph = _sec(LEAN["purlin"])
        for y in _even(lr["y"][0] + pw / 2, lr["y"][1] - pw / 2, LEAN["s"]):
            items.append(("purlin", LEAN["purlin"], (lr["x"][0], y, LEAN["top"] + rh), (lr["x"][1], y, LEAN["top"] + rh), (0, 0, 1)))
    return items


def _even(a, b, s):
    n = math.ceil((b - a) / s - 1e-9)
    return [a + i * (b - a) / n for i in range(n + 1)]


def _xy_ax(ax, u, v):
    return (u, v) if ax == 0 else (v, u)


def _xyz_ax(ax, u, v, z):
    return (*_xy_ax(ax, u, v), z)


def build_roof_frame():
    c = _clear(C_ROOF)
    steel = mat("M_Steel_C", (0.10, 0.10, 0.11), 0.45, 0.9)
    batten_m = mat("M_Galv", (0.62, 0.64, 0.66), 0.35, 0.9)
    counts = {}
    for kind, sec, p0, p1, up in _roof_layout():
        counts[kind] = counts.get(kind, 0) + 1
        name = f"RF_{kind}_{counts[kind]:03d}"
        _drop(bpy.data.meshes, name)
        bm = bmesh.new()
        L = _member(bm, sec, p0, p1, up)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(batten_m if kind == "batten" else steel)
        me["element"], me["type"], me["section"], me["kind"] = "steel", sec, sec, kind
        me["p0"], me["p1"], me["up"], me["th"] = list(p0), list(p1), list(up), _TH[kind]
        o = bpy.data.objects.new(name, me)
        c.objects.link(o)
    bpy.context.view_layer.update()
    return counts


_TH = {"plate": "อะเส/ขื่อเหล็ก", "ridge": "อกไก่เหล็ก", "hip": "ตะเข้สันเหล็ก", "valley": "ตะเข้รางเหล็ก",
       "post": "ดั้งเหล็ก", "rafter": "จันทันเหล็ก", "batten": "ระแนงเหล็กกัลวาไนซ์", "support": "เหล็กรับจันทัน (เพิง/กันสาด)",
       "lean_rafter": "จันทันเหล็ก (เพิง/กันสาด)", "purlin": "แปเหล็ก (เพิง/กันสาด)"}


def _members():
    """[(object, kind, section, p0, p1, length read from volume / section area)]."""
    out = []
    for o in _coll(C_ROOF).objects:
        me = o.data
        if not me or me.get("element") != "steel":
            continue
        bm = _world_bm(o)
        v = bm.calc_volume(signed=True)
        bm.free()
        out.append((o, me["kind"], me["section"], Vector(me["p0"]), Vector(me["p1"]), v / _sec_area(me["section"])))
    return out


def roof_report():
    by, out = {}, []
    for o, kind, sec, p0, p1, L in _members():
        by.setdefault((sec, kind), []).append(L)
    kgm = lambda sec: _sec_area(sec) * RHO
    tot = {}
    for (sec, kind), Ls in sorted(by.items()):
        m = sum(Ls)
        tot[sec] = tot.get(sec, []) + Ls
        out.append(f"{_TH[kind]} {sec}: {len(Ls)} ชิ้น = {m:.2f} ม. = {m * kgm(sec):.1f} กก.")
    for sec, Ls in sorted(tot.items()):
        pieces = []
        welds = 0
        for L in Ls:
            while L > ROOF["stock"] + 1e-9:
                pieces.append(ROOF["stock"])
                L -= ROOF["stock"]
                welds += 1
            pieces.append(L)
        k = SECTIONS[sec][0]
        n = _stock_bars(pieces, ROOF["stock"])
        out.append(f"รวม {sec}: {sum(Ls):.2f} ม. = {sum(Ls) * kgm(sec):.1f} กก. → เหล็กยาว 6 ม. {n * (2 if k == '2C' else 1)} เส้น"
                   f"{' (2C = 2 เส้น/ท่อน)' if k == '2C' else ''}, รอยต่อเชื่อม {welds}")
    return "\n".join(out)


# ---------------------------------------------------------------- ST07 selfcheck

def _check_roof(rows_before):
    def eq(a, b, what, rel=1e-4):
        assert abs(a - b) <= rel * max(abs(b), 1e-9), f"[{what}] model {a:.5f} != expected {b:.5f}"
    ms = _members()
    t, cth = _tan(), math.cos(math.radians(PITCH))
    m_w, m_h = _sec(ROOF["member"])
    kinds = {}
    for o, kind, sec, p0, p1, L in ms:
        kinds.setdefault(kind, []).append((o, sec, p0, p1, L))
        eq(L, (p1 - p0).length, "section", 2e-3)                  # volume / drawn section area = member length
    for k in ("plate", "ridge", "hip", "valley", "post", "rafter", "batten", "support", "lean_rafter", "purlin"):
        assert kinds.get(k), f"[count] no {k} in the roof frame"
    assert len(kinds["ridge"]) == 3 and len(kinds["valley"]) == 2, \
        f"[count] {len(kinds['ridge'])} ridges / {len(kinds['valley'])} valleys, S-05 has 3 / 2"
    assert len(kinds["post"]) == len(KING_POSTS), f"[count] {len(kinds['post'])} king posts, S-05 has {len(KING_POSTS)}"
    for o, sec, p0, p1, L in kinds["plate"]:
        assert abs(p0.z + m_h - PLATE_TOP) < 1e-5 and abs(p1.z - p0.z) < 1e-6, f"[plate] {o.name}: top {p0.z + m_h:.3f}"
    # rafters: pitch, seat on the plate's outer top edge, eave line, spacing ≤ s along every plane
    for o, sec, p0, p1, L in kinds["rafter"]:
        d = p1 - p0
        ang = math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
        assert abs(ang - PITCH) < 1e-3, f"[pitch] {o.name}: {ang:.3f}°"
    eave_r = [r for r in kinds["rafter"] if _roof_d(r[2].x, r[2].y) is not None and abs(_roof_d(r[2].x, r[2].y) - _eave_start()) < 1e-3]
    assert eave_r, "[eave] no rafter starts at the fascia back"
    for o, sec, p0, p1, L in eave_r:
        dd = _roof_d(p0.x, p0.y)
        z_edge = p0.z + (p1 - p0).z / (p1 - p0).xy.length * (-0.05 - dd)
        assert abs(z_edge - PLATE_TOP) < 1e-4, f"[seat] {o.name}: underside at the plate's outer edge {z_edge:.4f} != {PLATE_TOP}"
    # model spacing read back: rafter feet along each eave, where the eave between two feet belongs to that plane
    feet = {}
    for o, sec, p0, p1, L in eave_r:
        d = p1 - p0
        ax = 0 if abs(d.x) > abs(d.y) else 1
        dr = 1 if (d.x, d.y)[ax] > 0 else -1
        k = round((p0.x, p0.y)[ax] - dr * _eave_start(), 3)
        feet.setdefault((ax, k, dr), []).append((p0.y, p0.x)[ax])
    for P, vs in feet.items():
        P = (P[0], float(P[1]), P[2])
        vs = sorted(vs)
        for a, b in zip(vs, vs[1:]):
            mid = (a + b) / 2
            if _on(P, *_xy(P, P[1] + P[2] * _eave_start(), mid), 1e-6):
                assert b - a <= ROOF["rafter_s"] + 1e-4, f"[spacing] rafter feet {a:.2f} -> {b:.2f} on eave {P}"
    # battens: on the rafter tops, first course, spacing within CPAC's 0.32–batten_max
    for o, sec, p0, p1, L in kinds["batten"]:
        dd = _roof_d(p0.x, p0.y)
        assert abs(p0.z - _z_top(dd)) < 1e-4, f"[battens] {o.name}: not on the rafter tops"
    for p in _planes():
        ss = _batten_courses(p)
        assert abs(ss[0] - ROOF["batten_first"]) < 1e-6, "[battens] first course"
        gaps = [b - a for a, b in zip(ss, ss[1:])]
        assert max(gaps) <= ROOF["batten_max"] + 1e-6 and min(gaps) >= 0.30 - 1e-6, f"[battens] courses {min(gaps):.3f}..{max(gaps):.3f} on {p}"
    seen = {}
    for o, sec, p0, p1, L in kinds["batten"]:
        M = (p0 + p1) / 2
        dd = _roof_d(M.x, M.y)
        P = [q for q in _planes() if _on(q, M.x, M.y, 1e-6) and abs((p1 - p0).normalized()[q[0]]) < 1e-6]
        assert P, f"[battens] {o.name}: on no roof plane"
        sl = (dd + EAVE) / cth
        assert any(abs(sl - c_) < 1e-3 for c_ in _batten_courses(P[0])), f"[battens] {o.name}: {sl:.3f} up the slope, not a CPAC course"
        seen.setdefault(P[0], set()).add(round(sl, 3))
    for p, got in seen.items():
        assert any(abs(g - ROOF["batten_first"]) < 1e-3 for g in got), f"[battens] plane {p}: no batten {ROOF['batten_first']} up from the eave"
    # ridges / hips: top corners on the planes; valleys: top on the line
    for kind in ("ridge", "hip", "valley"):
        for o, sec, p0, p1, L in kinds[kind]:
            cphi = (p1 - p0).xy.length / (p1 - p0).length
            for P in (p0 + (p1 - p0) * 0.3, p0 + (p1 - p0) * 0.7):
                dd = _roof_d(P.x, P.y)
                top = P.z + m_h / cphi
                want = _z_top(dd) - (m_w / 2 * t if kind == "ridge" else m_w / 2 * t / math.sqrt(2) if kind == "hip" else 0)
                assert top >= want - 1e-4 and (kind != "ridge" or abs(top - want) < 1e-4) and top - want < 0.05, \
                    f"[planes] {o.name}: top {top:.4f} vs planes {want:.4f}"
    # king posts: on the tie top, up to the ridge underside
    rid = [(r[2], r[3]) for r in kinds["ridge"]]
    for o, sec, p0, p1, L in kinds["post"]:
        assert abs(p0.z - PLATE_TOP) < 1e-5, f"[posts] {o.name}: bottom {p0.z:.3f} != tie top {PLATE_TOP}"
        under = [a.z + (b.z - a.z) * ((Vector((p0.x, p0.y)) - a.xy).length / max((b - a).xy.length, 1e-9))
                 for a, b in rid if min(a.x, b.x) - 0.11 <= p0.x <= max(a.x, b.x) + 0.11 and min(a.y, b.y) - 0.11 <= p0.y <= max(a.y, b.y) + 0.11]
        assert under and abs(p1.z - under[0]) < 1e-3, f"[posts] {o.name}: top {p1.z:.3f} not at the ridge underside"
    # lean-to / canopy
    for o, sec, p0, p1, L in kinds["support"]:
        assert abs(p0.z + _sec(sec)[1] - LEAN["top"]) < 1e-5, f"[lean] {o.name}: support top {p0.z + _sec(sec)[1]:.3f} != {LEAN['top']}"
    for name, lr in LEAN_ROOFS.items():
        ys = sorted(p0.y for o, sec, p0, p1, L in kinds["purlin"] if lr["x"][0] - 1e-6 <= p0.x <= lr["x"][1] + 1e-6 and lr["y"][0] - 0.1 <= p0.y <= lr["y"][1] + 0.1)
        xs = sorted(p0.x for o, sec, p0, p1, L in kinds["lean_rafter"] if lr["x"][0] - 0.1 <= p0.x <= lr["x"][1] + 0.1 and abs(p0.y - lr["y"][0]) < 1e-6)
        assert len(ys) > 1 and max(b - a for a, b in zip(ys, ys[1:])) <= LEAN["s"] + 1e-6, f"[lean] {name}: purlins further than {LEAN['s']}"
        assert len(xs) > 1 and max(b - a for a, b in zip(xs, xs[1:])) <= LEAN["s"] + 1e-6, f"[lean] {name}: rafters further than {LEAN['s']}"
    # clash: oriented boxes of every pair of members (touching allowed)
    ob = []
    for o, kind, sec, p0, p1, L in ms:
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        d = (p1 - p0).normalized()
        ob.append((o.name, kind, obb(vs, d), [min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]))
    bad = []
    ob.sort(key=lambda q: q[3][0])
    for i, a in enumerate(ob):
        for b in ob[i + 1:]:
            if b[3][0] > a[4][0] + 1e-6:
                break
            if any(b[3][k] > a[4][k] + 1e-6 or a[3][k] > b[4][k] + 1e-6 for k in (1, 2)):
                continue
            dep = obb_overlap(a[2], b[2])
            if dep > 2e-3:
                bad.append((round(dep, 4), a[0], b[0]))
    assert not bad, f"[clash] {len(bad)} steel pairs overlap, worst {max(bad)}: {sorted(bad, reverse=True)[:30]}"
    # nothing of the frame inside the concrete / walls below
    below = [bx for (el, _), x in rows_before.items() if el not in ("excavation", "opening") for bx in x["boxes"]]
    hit = []
    for nm, kind, box, lo, hi in ob:
        for q in below:
            if q[5] > lo[2] + 1e-3 and q[2] < hi[2] - 1e-3 and q[3] > lo[0] + 1e-3 and q[0] < hi[0] - 1e-3 and q[4] > lo[1] + 1e-3 and q[1] < hi[1] - 1e-3:
                c = Vector(((q[0] + q[3]) / 2, (q[1] + q[4]) / 2, (q[2] + q[5]) / 2))
                qb = (c, [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))], [(q[3] - q[0]) / 2, (q[4] - q[1]) / 2, (q[5] - q[2]) / 2])
                dep = obb_overlap(box, qb)
                if dep > 2e-3:
                    hit.append((round(dep, 4), nm))
    assert not hit, f"[clash] {len(hit)} steel members inside concrete/brick/plaster, worst {max(hit)}: {sorted(hit, reverse=True)[:12]}"
    n = {k: len(v) for k, v in kinds.items()}
    return f"ST07 ok: " + ", ".join(f"{k} {v}" for k, v in n.items())
