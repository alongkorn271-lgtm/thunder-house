"""KK01 ST09 ฝ้าเพดาน (generic ST08 ceilings; numbered ST09 here because the roof covering took ST08) – exec'd after
kk01_cover.py.

A-02: CL1 ฝ้ายิปซัมบอร์ดธรรมดา 9 มม., CL2 ยิปซัมบอร์ดกันชื้น 9 มม., โครงเคร่าโลหะชุบสังกะสี @0.40×0.40, ฉาบเรียบ ทาสี.
A-04 room tags give the ceiling height above the room's floor: CL1 FL2 + 2.80, bath CL2 FL4 + 2.90 → all +3.60.
Kitchen and rear verandah (under the lean-to) carry no height: +3.10 (FL + 2.30, under the +3.175 wall tops; assumed).
Rooms are traced from the model: rays from a seed point at ceiling height to the first wall / plaster / column box
(practice `_room_rect`); columns proud of the wall are cut out of the boards.
Frame (assumed from "@0.40×0.40"): C-line cross runners along x @0.40 on the boards' backs, mains along y @0.40 on
top; hangers from the mains to the roof steel found by scanning every 2 cm (practice), gaps ≤ 1.00 m, ends ≤ 0.75 m,
a main within 0.30 m of a wall angle hangs from the angle (practice, assumed); main ends sit on the wall angle.
Eave soffit: SCG Smartboard vented 4 mm at fascia bottom + 1" (practice), between the fascia back and the outer
plaster, none under the lean-to; the front verandah between the wings is ceiled CL2 at the same level (A-04).
Soffit runners: 3 rows along every eave (fascia, 0.60 joint, wall), cross pieces @0.40.
Objects: CE_<room>_Board/_Frame/_Hangers, CE__soffit_Board/_Verandah/_Frame. Spec: ST09_ceilings_spec.md.
"""
from mathutils.bvhtree import BVHTree

CEIL = dict(board_t=0.009, sheet=(1.20, 2.40), waste=0.05, s_cross=0.40, s_main=0.40, first=0.05,
            cl=(0.036, 0.011), rod=0.006, hang=1.00, hang_end=1.00, scan=0.02, wall_free=0.30)
# hang_end: every main here ends on a wall angle (rooms are traced wall to wall), so the end gap is held like an
# inner gap (the usual 0.75 is for a free end)
SOFFIT = dict(t=0.004, above_fascia=0.0254, joint=0.60, s=0.40, edge=0.02, sheet=(0.60, 1.20),
              name="SCG Smartboard ระบายอากาศ 4 มม.")
CL_TYPES = {"CL1": "ฝ้ายิปซัมบอร์ดธรรมดา 9 มม.", "CL2": "ฝ้ายิปซัมบอร์ดกันชื้น 9 มม."}
ROOMS = [   # name, seed, ceiling level, type (A-04 tags; kitchen level assumed)
    ("bed1", (2.0, 6.0), 3.60, "CL1"), ("corridor", (3.0, 3.2), 3.60, "CL1"), ("dressing", (1.2, 1.2), 3.60, "CL1"),
    ("bath1", (1.2, 3.2), 3.60, "CL2"), ("storage", (4.2, 2.0), 3.60, "CL1"), ("living", (7.2, 4.0), 3.60, "CL1"),
    ("bed2", (11.2, 6.0), 3.60, "CL1"), ("bath2", (11.7, 3.7), 3.60, "CL2"), ("bed3", (11.2, 1.5), 3.60, "CL1"),
    ("kitchen", (6.5, 10.7), 3.10, "CL1")]
OPEN_ROOMS = [("verandah_rear", (3.385, 7.615, 9.615, 9.085), 3.10, "CL2")]   # between the column plaster lines (assumed)
LEANTO_X = (2.5, 10.5)                                 # no eave soffit under the lean-to
C_CEIL = "KK01 ST09 Ceilings"
STAGES.append(C_CEIL)


def _obstacles():
    """Wall / plaster / column boxes the rooms are traced in."""
    boxes = []
    for cn, els in ((C_WALL, ("brick", "concrete", "plaster")), (C_COL, ("concrete",))):
        for (el, _), x in qto(cn).items():
            if el in els:
                boxes += x["boxes"]
    return boxes


def _room_rect(seed, z, obst):
    x, y = seed
    hits = {}
    for ax, sg in ((0, 1), (0, -1), (1, 1), (1, -1)):
        best = None
        for b in obst:
            if not (b[2] <= z <= b[5]) or not (b[1 - ax] <= (y, x)[ax] <= b[4 - ax]):
                continue
            face = b[ax] if sg > 0 else b[ax + 3]
            if (face - (x, y)[ax]) * sg > -1e-9 and (best is None or (face - best) * sg < 0):
                best = face
        assert best is not None, f"room at {seed}: no wall {'+-'[sg < 0]}{'xy'[ax]}"
        hits[(ax, sg)] = best
    return hits[(0, -1)], hits[(1, -1)], hits[(0, 1)], hits[(1, 1)]


def _col_cuts(z):
    """Column + plaster footprints at height z (cut out of boards)."""
    tp = PLASTER["t"]
    return [(c[0] - tp, c[1] - tp, c[3] + tp, c[4] + tp) for c in _col_prisms().values() if c[2] <= z <= c[5] + 1e-6]


def _rects_minus(rects, cuts):
    out = []
    for r in rects:
        pcs = [(r[0], r[1], 0.0, r[2], r[3], 1.0)]
        for c in cuts:
            pcs = [q for p in pcs for q in _box_minus(p, (c[0], c[1], -1.0, c[2], c[3], 2.0))]
        out += [(q[0], q[1], q[3], q[4]) for q in pcs if q[3] - q[0] > 1e-6 and q[4] - q[1] > 1e-6]
    return out


def _rects_and(rects, clip):
    out = []
    for r in rects:
        a, b, c, d = max(r[0], clip[0]), max(r[1], clip[1]), min(r[2], clip[2]), min(r[3], clip[3])
        if c - a > 1e-6 and d - b > 1e-6:
            out.append((a, b, c, d))
    return out


def _ceiling_rooms():
    """name -> (level, type, [board rects], traced rect) — overlaps removed in table order."""
    obst = _obstacles()
    placed, out = [], {}
    for name, seed, lvl, tp in ROOMS:
        r = _room_rect(seed, lvl - 0.05, obst)
        pcs = _rects_minus([r], placed + _col_cuts(lvl))
        out[name] = (lvl, tp, pcs, r)
        placed += pcs
    for name, r, lvl, tp in OPEN_ROOMS:
        pcs = _rects_minus([r], placed + _col_cuts(lvl))
        out[name] = (lvl, tp, pcs, r)
        placed += pcs
    vp = _soffit_pieces()[1]                                # front verandah: CL2 at the soffit level, framed + hung
    out["verandah_front"] = (_soffit_level(), "CL2", vp, (min(p[0] for p in vp), min(p[1] for p in vp),
                                                          max(p[2] for p in vp), max(p[3] for p in vp)))
    return out


def _soffit_level():
    return _bed_z(-EAVE) - FASCIA["h"] + SOFFIT["above_fascia"]


def _footprint_outer():
    """(enclosed house rect, open front verandah rect) in plan, at the outer plaster faces."""
    o = COL["b"] / 2 + PLASTER["t"]
    main = (-o, -o, 13.0 + o, 7.5 + o)
    ver = (5.0 + BRICK["t"] / 2 + PLASTER["t"], -o, 9.5 - BRICK["t"] / 2 - PLASTER["t"],
           1.0 - (COL["b"] / 2 - BRICK["t"] / 2) - BRICK["t"] / 2 - PLASTER["t"])
    return main, ver


def _soffit_pieces():
    """(soffit rects, front-verandah rects): inside the fascia backs, outside the house, not under the lean-to, round
    the columns."""
    inner = [(q[0], q[1], q[3], q[4]) for q in
             _disjoint([(r[0] + FASCIA_T, r[1] + FASCIA_T, 0.0, r[2] - FASCIA_T, r[3] - FASCIA_T, 1.0) for r in _outline_rects()])]
    main, ver = _footprint_outer()
    lean = (LEANTO_X[0], main[3], LEANTO_X[1], 99.0)
    allp = _rects_minus(inner, [lean] + _col_cuts(_soffit_level()))
    return _rects_minus(allp, [main]), [q for p in allp for q in _rects_and([p], ver)]


def _clip_line(ax, k, rects):
    """Merged intervals of the line along axis ax at other-coordinate k inside the union of rects."""
    iv = sorted(((r[0], r[2]) if ax == 0 else (r[1], r[3])) for r in rects
                if ((r[1], r[0])[ax] - 1e-9 <= k <= (r[3], r[2])[ax] + 1e-9))
    out = []
    for a, b in iv:
        if out and a <= out[-1][1] + 1e-6:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return [(a, b) for a, b in out if b - a > 1e-3]


def _steel_bvh():
    V, P = [], []
    for o in _coll(C_ROOF).objects:
        if o.data and o.data.get("element") == "steel":
            M = o.matrix_world
            base = len(V)
            V += [M @ v.co for v in o.data.vertices]
            P += [[base + i for i in p.vertices] for p in o.data.polygons]
    return BVHTree.FromPolygons(V, P)


def _hang_points(bvh, x, a, b, z0, room_x0, room_x1):
    """Hangers along a main at x from y a to b, top of main z0: the steel crossings found every scan step, picked so
    gaps stay ≤ hang and the ends ≤ hang_end; over a gap with no steel the hanger goes in with a sideways link.
    → [(y, z of the steel, link length)]"""
    c = CEIL
    if x - room_x0 < c["wall_free"] or room_x1 - x < c["wall_free"]:
        return []
    up = Vector((0, 0, 1))
    n = max(1, int((b - a) / c["scan"]))
    hits = []
    for i in range(n + 1):
        u = a + (b - a) * i / n
        h = bvh.ray_cast(Vector((x, u, z0)), up, 3.0)
        if h[0] is not None:
            hits.append((u, h[0].z))
    out, cur, first = [], a, True
    while b - cur > c["hang_end"] + 1e-9:
        reach = cur + (c["hang_end"] if first else c["hang"]) + c["scan"]
        cand = [h for h in hits if cur + 1e-9 < h[0] <= reach]
        if cand:
            out.append((*cand[-1], 0.0))
        else:
            u = min(cur + (c["hang_end"] if first else c["hang"]), b)
            for dx in [sg * 0.05 * i for i in range(1, 21) for sg in (1, -1)]:   # sideways link up to 1.00 m
                h = bvh.ray_cast(Vector((x + dx, u, z0)), up, 3.0)
                if h[0] is not None:
                    out.append((u, h[0].z, abs(dx)))
                    break
            else:
                raise AssertionError(f"no steel within 1.0 m over the main at ({x:.2f}, {u:.2f})")
        cur, first = out[-1][0], False
    return out


def _eave_depth(ax, k, a, b, side, sp):
    """Depth of the soffit along an eave: fascia back → the end of the soffit going in, at the eave's middle."""
    back = k + side * FASCIA_T
    cap = EAVE - FASCIA_T - (COL["b"] / 2 + PLASTER["t"])   # fascia back → the house face: beyond it is another eave
    for v0, v1 in _clip_line(1 - ax, (a + b) / 2, sp):
        if v0 - 1e-6 <= back + side * 0.01 <= v1 + 1e-6:
            return min((v1 - back) if side > 0 else (back - v0), cap)
    return None


def _ceiling_layout():
    c = CEIL
    bvh = _steel_bvh()
    lay = {}
    w = c["cl"][0] / 2
    for name, (lvl, tp, pcs, r) in _ceiling_rooms().items():
        z_cross = lvl + c["board_t"]
        z_main = z_cross + c["cl"][1]
        frame, hangers = [], []
        x0, y0 = min(p[0] for p in pcs), min(p[1] for p in pcs)
        x1, y1 = max(p[2] for p in pcs), max(p[3] for p in pcs)
        for y in _even(y0 + c["first"], y1 - c["first"], c["s_cross"]):          # cross runners along x
            for a, b in _clip_line(0, y, pcs):
                frame.append(("cross", (a, y - w, z_cross, b, y + w, z_main)))
        for x in _even(x0 + c["first"], x1 - c["first"], c["s_main"]):           # mains along y on top
            for a, b in _clip_line(1, x, pcs):
                frame.append(("main", (x - w, a, z_main, x + w, b, z_main + c["cl"][1])))
                hangers += [(x, u, z_main + c["cl"][1], zt, link) for u, zt, link in _hang_points(bvh, x, a, b, z_main + c["cl"][1], x0, x1)]
        lay[name] = dict(level=lvl, type=tp, boards=[(p[0], p[1], lvl, p[2], p[3], z_cross) for p in pcs], frame=frame,
                         hangers=hangers, rect=r, perimeter=2 * ((r[2] - r[0]) + (r[3] - r[1])))
    zs = _soffit_level()
    zf = zs + SOFFIT["t"]
    sp, vp = _soffit_pieces()
    s_frame = []
    for ax, k, a, b, side in _outline_edges():
        dep = _eave_depth(ax, k, a, b, side, sp)
        if dep is None:
            continue
        back = k + side * FASCIA_T
        e = SOFFIT["edge"]
        for v in sorted({e, max(e, dep - SOFFIT["joint"]), dep - e}):               # fascia row, 0.60 joint, wall row
            kk = back + side * v
            for u0, u1 in _clip_line(ax, kk, sp):
                u0, u1 = max(u0, a), min(u1, b)
                if u1 - u0 > 0.05:
                    s_frame.append(("soffit_runner", _box(ax, u0, u1, kk - w, kk + w, zf, zf + c["cl"][1])))
        lo, hi = sorted((back + side * (e + w), back + side * (dep - e - w)))
        for u in _even(a + 0.05, b - 0.05, SOFFIT["s"]):                            # cross pieces between them
            for v0, v1 in _clip_line(1 - ax, u, sp):
                v0, v1 = max(v0, lo), min(v1, hi)
                if v1 - v0 > 0.05:
                    s_frame.append(("soffit_cross", _box(ax, u - w, u + w, v0, v1, zf, zf + c["cl"][1])))
    lay["_soffit"] = dict(level=zs, boards=[(p[0], p[1], zs, p[2], p[3], zf) for p in sp], frame=s_frame)
    return lay


def build_ceilings():
    c = _clear(C_CEIL)
    gyp = mat("M_Gypsum", (0.95, 0.95, 0.93), 0.8)
    gyp2 = mat("M_GypsumMR", (0.86, 0.92, 0.88), 0.8)
    sb = mat("M_Smartboard", (0.70, 0.70, 0.68), 0.85)
    fr = mat("M_CLine", (0.75, 0.77, 0.80), 0.4, 0.8)
    for name, d in _ceiling_layout().items():
        root = bpy.data.objects.new(f"CE_{name}", None)
        c.objects.link(root)
        if name == "_soffit":
            parts = {"Board": _boxes_data("CE__soffit_Board", d["boards"], sb, element="soffit", type="SF", th=SOFFIT["name"]),
                     "Frame": _boxes_data("CE__soffit_Frame", [b for _, b in d["frame"]], fr, element="cline", type="SF",
                                          th="โครงซีไลน์ฝ้าชายคา")}
        else:
            parts = {"Board": _boxes_data(f"CE_{name}_Board", d["boards"], gyp if d["type"] == "CL1" else gyp2, element="ceiling",
                                          type=d["type"], th=CL_TYPES[d["type"]], level=d["level"], room=name),
                     "Frame": _boxes_data(f"CE_{name}_Frame", [b for _, b in d["frame"]], fr, element="cline", type="CE",
                                          th="โครงซีไลน์ฝ้า")}
            if d["hangers"]:
                parts["Hangers"] = _rebar_data(f"CE_{name}_Hangers", [[(x, u, z0), (x, u, zt)] for x, u, z0, zt, l in d["hangers"]],
                                               CEIL["rod"], fr, element="hanger", type="CE", th="ก้านแขวนฝ้า", bar="rod",
                                               dia_mm=6, links=sum(1 for *_, l in d["hangers"] if l > 0))
        for k, data in parts.items():
            ob = bpy.data.objects.new(f"{root.name}_{k}", data)
            ob.parent = root
            c.objects.link(ob)
    bpy.context.view_layer.update()
    return len(_coll(C_CEIL).objects)


def ceiling_report():
    r = qto(C_CEIL)
    out = []
    sh = CEIL["sheet"][0] * CEIL["sheet"][1]
    for tp in ("CL1", "CL2"):
        x = r.get(("ceiling", tp))
        if x:
            A = x["vol"] / CEIL["board_t"]
            out.append(f"{CL_TYPES[tp]}: {A:.2f} ตร.ม. → แผ่น 1.20×2.40 {math.ceil(A / sh * (1 + CEIL['waste']) - 1e-9)} แผ่น (+5 %)")
    x = r.get(("soffit", "SF"))
    if x:
        A = x["vol"] / SOFFIT["t"]
        s = SOFFIT["sheet"][0] * SOFFIT["sheet"][1]
        out.append(f"ฝ้าชายคา {SOFFIT['name']}: {A:.2f} ตร.ม. → แผ่น 0.60×1.20 {math.ceil(A / s * (1 + CEIL['waste']) - 1e-9)} แผ่น (+5 %)")
    cl = sum(max(b[3] - b[0], b[4] - b[1]) for (el, _), x in r.items() if el == "cline" for b in x["boxes"])
    out.append(f"โครงซีไลน์ (ฝ้าใน + ชายคา): {cl:.2f} ม. → ยาว 4 ม. {math.ceil(cl / 4.0 * 1.05 - 1e-9)} เส้น (+5 %)")
    hg = r.get(("hanger", "CE"))
    links = sum(o.data.get("links", 0) for o in _coll(C_CEIL).objects if o.data and o.data.get("element") == "hanger")
    if hg:
        out.append(f"ก้านแขวน: {len(hg['bars'])} จุด รวม {sum(hg['bars']):.2f} ม. (ต่อด้านข้าง {links} จุด)")
    rooms = _ceiling_rooms()
    per = sum(2 * ((rr[2] - rr[0]) + (rr[3] - rr[1])) for n, (l, t, p, rr) in rooms.items())
    out.append(f"ฉากริมผนัง (wall angle): ≈ {per:.2f} ม. → ยาว 3 ม. {math.ceil(per / 3.0 * 1.05 - 1e-9)} เส้น")
    pl = qto(C_WALL).get(("plaster", "PL"), dict(boxes=[]))["boxes"]
    above = 0.0
    for n, (lvl, t, p, rr) in rooms.items():
        if n not in {r_[0] for r_ in ROOMS}:
            continue                                      # verandahs are outside: their walls keep plaster to the top
        clip = (rr[0] - 0.02, rr[1] - 0.02, lvl, rr[2] + 0.02, rr[3] + 0.02, 99.0)
        above += sum(_vol(i) for b in pl if (i := _inter(b, clip))) / PLASTER["t"]
    out.append(f"ฉาบในเหนือระดับฝ้าที่ยังเหลือใน ST06: {above:.2f} ตร.ม. (ควรเป็น 0: ST06 หยุดฉาบในที่ฝ้าแล้ว)")
    return "\n".join(out)


# ---------------------------------------------------------------- ST09 selfcheck

def _check_ceilings(rows_before):
    def eq(a, b, what, rel=1e-4):
        assert abs(a - b) <= rel * max(abs(b), 1e-9), f"[{what}] model {a:.4f} != expected {b:.4f}"
    objs = {o.name: o for o in _coll(C_CEIL).objects}

    def boxes(name):
        if name not in objs:
            return []
        bm = _world_bm(objs[name])
        try:
            return _obj_boxes(bm, name)
        finally:
            bm.free()
    obst, bvh, c = _obstacles(), _steel_bvh(), CEIL
    placed = []

    def room(item):
        name, seed, lvl, tp = item
        bd = boxes(f"CE_{name}_Board")
        assert bd, f"[count] no ceiling in {name}"
        for b in bd:
            assert abs(b[2] - lvl) < 1e-5 and abs(b[5] - b[2] - c["board_t"]) < 1e-5, f"[level] {name}: board at {b[2]:.3f}, spec {lvl}"
        if name == "verandah_front":
            want = _soffit_pieces()[1]
        else:
            r = _room_rect(seed, lvl - 0.05, obst) if seed else [x for n, x, l, t in OPEN_ROOMS if n == name][0]
            want = _rects_minus([r], placed + _col_cuts(lvl))   # the room traced again from the walls in the model
        placed.extend(want)
        eq(sum((b[3] - b[0]) * (b[4] - b[1]) for b in bd), sum((p[2] - p[0]) * (p[3] - p[1]) for p in want), "boards")
        for b in bd:
            got = sum(max(0, min(b[3], p[2]) - max(b[0], p[0])) * max(0, min(b[4], p[3]) - max(b[1], p[1])) for p in want)
            ab = (b[3] - b[0]) * (b[4] - b[1])
            assert abs(got - ab) < 1e-5 * ab + 1e-7, f"[boards] {name}: a board reaches outside the room"
        fr = boxes(f"CE_{name}_Frame")
        cross = [f for f in fr if f[3] - f[0] > f[4] - f[1]]
        mains = [f for f in fr if f[3] - f[0] <= f[4] - f[1]]
        for f in cross:
            assert abs(f[2] - (lvl + c["board_t"])) < 1e-5, f"[runners] {name}: cross runner not on the boards"
        for f in mains:
            assert abs(f[2] - (lvl + c["board_t"] + c["cl"][1])) < 1e-5, f"[runners] {name}: main not on the cross runners"
        for b in bd:   # runners both ways no further apart than spec over every board piece
            for lst, ax, s in ((cross, 1, c["s_cross"]), (mains, 0, c["s_main"])):
                if b[ax + 3] - b[ax] < 2 * s:
                    continue
                mid = (b[1 - ax] + b[4 - ax]) / 2
                pos = sorted((f[ax] + f[ax + 3]) / 2 for f in lst if f[1 - ax] - 1e-6 <= mid <= f[4 - ax] + 1e-6
                             and b[ax] - 1e-6 <= (f[ax] + f[ax + 3]) / 2 <= b[ax + 3] + 1e-6)
                edges = [b[ax]] + pos + [b[ax + 3]]
                assert max(q - p for p, q in zip(edges, edges[1:])) <= s + c["first"] + 1e-4, \
                    f"[runners] {name}: {'xy'[ax]} runners further than {s} over a board"
        if f"CE_{name}_Hangers" in objs:
            hs = _world_bars(objs[f"CE_{name}_Hangers"])
            for sp in hs:
                top, bot = sp[-1], sp[0]
                h = bvh.ray_cast(top - Vector((0, 0, 0.002)), Vector((0, 0, 1)), 0.01)
                assert h[0] is not None, f"[hangers] {name}: hanger top ({top.x:.2f}, {top.y:.2f}, {top.z:.3f}) not on steel"
                assert any(m[0] - 1e-5 <= bot.x <= m[3] + 1e-5 and m[1] - 1e-5 <= bot.y <= m[4] + 1e-5 and abs(m[5] - bot.z) < 1e-5
                           for m in mains), f"[hangers] {name}: hanger foot not on a main"
        else:
            hs = []
        bx0, bx1 = min(b[0] for b in bd), max(b[3] for b in bd)
        for m in mains:   # every main away from the wall angles hangs at ≤ hang, ends ≤ hang_end
            x = (m[0] + m[3]) / 2
            if x - bx0 < c["wall_free"] or bx1 - x < c["wall_free"]:
                continue
            us = sorted(sp[0].y for sp in hs if abs(sp[0].x - x) < 1e-4 and m[1] - 1e-6 <= sp[0].y <= m[4] + 1e-6)
            edges = [m[1]] + us + [m[4]]
            gaps = [q - p for p, q in zip(edges, edges[1:])]
            assert gaps[0] <= c["hang_end"] + c["scan"] + 1e-4 and gaps[-1] <= c["hang_end"] + c["scan"] + 1e-4 and \
                max(gaps[1:-1] or [0]) <= c["hang"] + c["scan"] + 1e-4, f"[hangers] {name}: main at x {x:.2f}: gaps {[round(g, 2) for g in gaps]}"
    _each(ROOMS + [(n, None, l, t) for n, r, l, t in OPEN_ROOMS] + [("verandah_front", None, _soffit_level(), "CL2")], room, "ceilings")
    # soffit: level; every point of the open eave closed by a board (grid probe, independent of the layout)
    zs = _soffit_level()
    sbd, vbd = boxes("CE__soffit_Board"), boxes("CE_verandah_front_Board")
    assert sbd and vbd, "[soffit] no eave soffit / verandah ceiling"
    for b in sbd:
        assert abs(b[2] - zs) < 1e-5 and abs(b[5] - b[2] - SOFFIT["t"]) < 1e-5, f"[soffit] at {b[2]:.3f}, fascia bottom + 1\" = {zs:.3f}"
    for b in vbd:
        assert abs(b[2] - zs) < 1e-5, f"[soffit] verandah ceiling at {b[2]:.3f} != soffit {zs:.3f}"
    main, ver = _footprint_outer()
    cols = _col_cuts(zs)
    rs = _outline_rects()
    miss = 0
    step = 0.05
    for i in range(int((max(r[2] for r in rs) - min(r[0] for r in rs)) / step) + 1):
        x = min(r[0] for r in rs) + step / 2 + i * step
        for j in range(int((max(r[3] for r in rs) - min(r[1] for r in rs)) / step) + 1):
            y = min(r[1] for r in rs) + step / 2 + j * step
            if not any(r[0] + FASCIA_T < x < r[2] - FASCIA_T and r[1] + FASCIA_T < y < r[3] - FASCIA_T for r in rs):
                continue
            in_house = main[0] < x < main[2] and main[1] < y < main[3] and not (ver[0] < x < ver[2] and ver[1] < y < ver[3])
            if in_house or (LEANTO_X[0] < x < LEANTO_X[1] and y > main[3]) or any(q[0] < x < q[2] and q[1] < y < q[3] for q in cols):
                continue
            if not any(b[0] <= x <= b[3] and b[1] <= y <= b[4] for b in sbd + vbd):
                miss += 1
    assert miss == 0, f"[soffit] {miss} probe points of the open eave not closed by a board"
    sp_spec = _soffit_pieces()[0]
    eq(sum((b[3] - b[0]) * (b[4] - b[1]) for b in sbd), sum((p[2] - p[0]) * (p[3] - p[1]) for p in sp_spec), "soffit")
    runners = boxes("CE__soffit_Frame")
    for f in runners:
        assert abs(f[2] - (zs + SOFFIT["t"])) < 1e-5, "[soffit] soffit runner not on the boards"
    sp, vp = _soffit_pieces()
    for ax, k, a, b, side in _outline_edges():   # each eave with soffit has its fascia-side runner over its length
        dep = _eave_depth(ax, k, a, b, side, sp)
        if dep is None:
            continue
        kk = k + side * (FASCIA_T + SOFFIT["edge"])
        cover = sorted((f[ax], f[ax + 3]) for f in runners if abs((f[1 - ax] + f[4 - ax]) / 2 - kk) < 1e-4
                       and f[ax + 3] - f[ax] > f[4 - ax] - f[1 - ax])
        want = [(max(u0, a), min(u1, b)) for u0, u1 in _clip_line(ax, kk, sp) if min(u1, b) - max(u0, a) > 0.05]
        got = sum(min(q, w1) - max(p, w0) for w0, w1 in want for p, q in cover if min(q, w1) > max(p, w0))
        assert abs(got - sum(w1 - w0 for w0, w1 in want)) < 1e-3, f"[soffit] eave {'xy'[ax]}={k}: fascia runner {got:.2f} of {sum(w1 - w0 for w0, w1 in want):.2f} m"
    solids = [bx for (el, _), x in rows_before.items() if el not in ("excavation", "opening") for bx in x["boxes"]]
    mine = [b for n in objs if n.endswith(("_Board", "_Verandah")) for b in boxes(n)]
    cl = [(a, b) for a in mine for b in _near(a, solids) if (i := _inter(a, b)) and _vol(i) > 1e-7 and min(i[k + 3] - i[k] for k in range(3)) > 1e-5]
    assert not cl, f"[clash] {len(cl)} ceiling boards inside walls/columns/plaster: {cl[0]}"
    return f"ST09 ok: {len(ROOMS) + len(OPEN_ROOMS)} ceilings, soffit at +{zs:.3f} {sum((b[3] - b[0]) * (b[4] - b[1]) for b in sbd):.2f} m²"
