"""KK01 ST10 รองพื้น + สี (generic ST09 primer, ST10 coat 1, ST13 coat 2 in one module; site order: primer and coat 1
after the ceilings, coat 2 after the electrics) – exec'd after kk01_ceiling.py.

A-02 wall types: 1 ฉาบเรียบ ทาสีอะคริลิคภายนอก TOA SuperShield, 2 ภายใน TOA SuperShield, 3 ฉาบ 2 ด้าน กรุกระเบื้องเคลือบ
8"×10" (bathrooms to the ceiling: ST11 tiles, built before the paint, cover them — no paint there), 4 ไม้เทียม (positions only on elevations — not
modelled). CL1/CL2 ceilings "ฉาบเรียบ ทาสี"; the eave soffit is painted with the exterior paint (practice).
Seen faces from the model (practice): every face of a plaster piece, less where any solid / other plaster / a ceiling or
soffit board (and all above it) stands within 3 mm in front; horizontal faces only inside openings (sills, heads).
Films stand 0.5 mm off the surface and off each other: primer (k=1), coat 1 (k=2), coat 2 (k=3, no `element`: coat 1's
row counts both coats). Quantities follow the contractor's formulas (practice): wall primer = the plaster area (ST06),
paint buckets = area ÷ 43.75 m² (TOA, 2 coats), ceilings ÷ 87.5 m².
Objects: PT_Primer, PT_Coat1, PT_Coat2, PT_CeilPrimer, PT_CeilPaint. Spec: ST10_paint_spec.md.
"""

PAINT = dict(film=0.0005, film_t=0.0003, reach=0.003, wall_m2=43.75, ceil_m2=87.5, primer_m2=87.5,
             ext="TOA SuperShield ภายนอก", int="TOA SuperShield ภายใน", ceil="สีฝ้า (ยิปซัม/สมาร์ทบอร์ด)")
_tile_cover = [True]                                   # ST11 reads the faces as plastered (its tiles not covers)
C_PAINT = "KK01 ST10 Paint"
STAGES.append(C_PAINT)


class _Grid:
    """Uniform 2D grid over boxes for neighbour queries."""
    def __init__(self, boxes, cell=0.5):
        self.c, self.b, self.g = cell, boxes, {}
        for i, b in enumerate(boxes):
            for gx in range(int(math.floor(b[0] / cell)), int(math.floor(b[3] / cell)) + 1):
                for gy in range(int(math.floor(b[1] / cell)), int(math.floor(b[4] / cell)) + 1):
                    self.g.setdefault((gx, gy), []).append(i)

    def near(self, q, pad=1e-6):
        c, seen, out = self.c, set(), []
        for gx in range(int(math.floor((q[0] - pad) / c)), int(math.floor((q[3] + pad) / c)) + 1):
            for gy in range(int(math.floor((q[1] - pad) / c)), int(math.floor((q[4] + pad) / c)) + 1):
                for i in self.g.get((gx, gy), ()):
                    if i not in seen:
                        seen.add(i)
                        b = self.b[i]
                        if b[0] < q[3] + pad and b[3] > q[0] - pad and b[1] < q[4] + pad and b[4] > q[1] - pad and b[2] < q[5] + pad and b[5] > q[2] - pad:
                            out.append(b)
        return out


def _faces(b):
    """(axis, sign, plane, rect in the other two axes (lo0, lo1, hi0, hi1)) for the 6 faces of box b."""
    out = []
    for ax in range(3):
        o = [i for i in range(3) if i != ax]
        rect = (b[o[0]], b[o[1]], b[o[0] + 3], b[o[1] + 3])
        out.append((ax, -1, b[ax], rect))
        out.append((ax, 1, b[ax + 3], rect))
    return out


def _paint_sources():
    plaster = qto(C_WALL)[("plaster", "PL")]["boxes"]
    solids = []
    for cn in (C_GB, C_FLOOR, C_COL, C_WALL):
        for (el, _), x in qto(cn).items():
            if el not in ("excavation", "opening"):
                solids += x["boxes"]
    ct = bpy.data.collections.get(globals().get("C_TILE", ""))
    if ct and _tile_cover[0]:   # ST11 finishes (built first): floor screed / bed / tiles at the wall feet, the bath wall tiles
        for o in ct.objects:
            if o.type == "MESH" and o.data.get("element") not in (None, "excavation", "mesh"):
                bm = _world_bm(o)
                try:
                    solids += _obj_boxes(bm, o.name)
                finally:
                    bm.free()
    boards = [b for (el, _), x in qto(C_CEIL).items() if el in ("ceiling", "soffit") for b in x["boxes"]]
    covers = solids + [(b[0], b[1], b[2], b[3], b[4], 99.0) for b in boards]   # a board hides everything above it
    opens = [b for (el, _), x in qto(C_WALL).items() if el == "opening" for b in x["boxes"]]
    return plaster, covers, opens, boards


def _seen_faces():
    """[(axis, sign, plane, [rects])] seen parts of the plaster faces (see module doc)."""
    plaster, covers, opens, _ = _paint_sources()
    grid = _Grid(covers)
    tp, r = PLASTER["t"], PAINT["reach"]
    out = []
    for b in plaster:
        for ax, sg, pl, rect in _faces(b):
            if ax == 2:   # horizontal: only sills / heads inside an opening
                c = ((rect[0] + rect[2]) / 2, (rect[1] + rect[3]) / 2)
                if not any(o[0] - tp - 1e-6 <= c[0] <= o[3] + tp + 1e-6 and o[1] - tp - 1e-6 <= c[1] <= o[4] + tp + 1e-6
                           and o[2] - tp - 1e-6 <= pl <= o[5] + tp + 1e-6 for o in opens):
                    continue
            o = [i for i in range(3) if i != ax]
            slab = [0.0] * 6
            slab[o[0]], slab[o[0] + 3], slab[o[1]], slab[o[1] + 3] = rect[0], rect[2], rect[1], rect[3]
            slab[ax], slab[ax + 3] = (pl, pl + r) if sg > 0 else (pl - r, pl)
            slab = tuple(slab)
            cuts = []
            for q in grid.near(slab):
                if q is b:
                    continue
                i = _inter(slab, q)
                if i and min(i[k + 3] - i[k] for k in range(3)) > 1e-7:
                    cuts.append((i[o[0]], i[o[1]], i[o[0] + 3], i[o[1] + 3]))
            pcs = _rects_minus([rect], cuts)
            pcs = [p for p in pcs if (p[2] - p[0]) > 1e-4 and (p[3] - p[1]) > 1e-4]
            if pcs:
                out.append((ax, sg, pl, pcs))
    return out


def _film(ax, sg, pl, p, k):
    """Film k (1 = primer) over face rect p: a 0.3 mm box standing k × 0.5 mm off the plane."""
    f, t = PAINT["film"], PAINT["film_t"]
    o = [i for i in range(3) if i != ax]
    b = [0.0] * 6
    b[o[0]], b[o[0] + 3], b[o[1]], b[o[1] + 3] = p[0], p[2], p[1], p[3]
    a0 = pl + sg * (k * f - t)
    a1 = pl + sg * (k * f)
    b[ax], b[ax + 3] = min(a0, a1), max(a0, a1)
    return tuple(b)


def _room_of_face(ax, sg, pl, p, rooms):
    """The enclosed room (ST09 ROOMS) the face looks into, or None (outside / verandah / laundry)."""
    o = [i for i in range(3) if i != ax]
    pt = [0.0] * 3
    pt[o[0]], pt[o[1]] = (p[0] + p[2]) / 2, (p[1] + p[3]) / 2
    pt[ax] = pl + sg * 0.05
    for name, (lvl, tp, pcs, rr) in rooms.items():
        if name in {r_[0] for r_ in ROOMS} and rr[0] <= pt[0] <= rr[2] and rr[1] <= pt[1] <= rr[3] and pt[2] <= lvl + 0.01:
            return name
    return None


def _paint_layout():
    faces = _seen_faces()
    rooms = _ceiling_rooms()
    primer, coat1, coat2, kinds = [], [], [], []
    for ax, sg, pl, pcs in faces:
        for p in pcs:
            room = _room_of_face(ax, sg, pl, p, rooms)
            primer.append(_film(ax, sg, pl, p, 1))
            coat1.append(_film(ax, sg, pl, p, 2))
            coat2.append(_film(ax, sg, pl, p, 3))
            kinds.append("int" if room else "ext")
    _, _, _, boards = _paint_sources()
    cp = [(b[0], b[1], b[2] - PAINT["film"], b[3], b[4], b[2] - PAINT["film"] + PAINT["film_t"]) for b in boards]
    cc = [(b[0], b[1], b[2] - 2 * PAINT["film"], b[3], b[4], b[2] - 2 * PAINT["film"] + PAINT["film_t"]) for b in boards]
    return dict(primer=primer, coat1=coat1, coat2=coat2, kinds=kinds, ceil_primer=cp, ceil_paint=cc)


def build_paint():
    c = _clear(C_PAINT)
    pm = mat("M_Primer", (0.92, 0.92, 0.90), 0.9)
    ext = mat("M_PaintExt", (0.80, 0.80, 0.78), 0.6)
    inn = mat("M_PaintInt", (0.96, 0.95, 0.91), 0.6)
    cl = mat("M_PaintCeil", (0.98, 0.98, 0.98), 0.7)
    L = _paint_layout()
    ext_b = [b for b, k in zip(L["coat1"], L["kinds"]) if k == "ext"]
    int_b = [b for b, k in zip(L["coat1"], L["kinds"]) if k == "int"]
    parts = {
        "PT_Primer": _boxes_data("PT_Primer", L["primer"], pm, element="paint", type="primer", th="สีรองพื้นปูนใหม่ (ผนัง)"),
        "PT_Coat1Ext": _boxes_data("PT_Coat1Ext", ext_b, ext, element="paint", type="ext", th=f"สีจริง {PAINT['ext']} 2 เที่ยว"),
        "PT_Coat1Int": _boxes_data("PT_Coat1Int", int_b, inn, element="paint", type="int", th=f"สีจริง {PAINT['int']} 2 เที่ยว"),
        "PT_Coat2": _boxes_data("PT_Coat2", L["coat2"], inn, coat=2),       # no element: coat 1's rows count both coats
        "PT_CeilPrimer": _boxes_data("PT_CeilPrimer", L["ceil_primer"], pm, element="paint", type="ceil_primer", th="สีรองพื้นฝ้า"),
        "PT_CeilPaint": _boxes_data("PT_CeilPaint", L["ceil_paint"], cl, element="paint", type="ceil", th=f"{PAINT['ceil']} 2 เที่ยว"),
    }
    for n, data in parts.items():
        if data is not None and len(data.vertices):
            c.objects.link(bpy.data.objects.new(n, data))
    bpy.context.view_layer.update()
    return len(L["primer"])


def _film_area(boxes):
    return sum(max((b[3] - b[0]) * (b[4] - b[1]), (b[3] - b[0]) * (b[5] - b[2]), (b[4] - b[1]) * (b[5] - b[2])) for b in boxes)


def paint_report():
    r = qto(C_PAINT)
    A = {tp: _film_area(x["boxes"]) for (el, tp), x in r.items()}
    pl_area = qto(C_WALL)[("plaster", "PL")]["vol"] / PLASTER["t"]
    out = [f"สีรองพื้นผนัง (สูตรผู้รับเหมา = พื้นที่ฉาบ ST06): {pl_area:.2f} ตร.ม. (ผิวที่มองเห็นจริง {A.get('primer', 0):.2f} ตร.ม.)",
           f"สีจริงผนังภายนอก {PAINT['ext']} 2 เที่ยว: {A.get('ext', 0):.2f} ตร.ม. → {math.ceil(A.get('ext', 0) / PAINT['wall_m2'] - 1e-9)} ถัง (÷ {PAINT['wall_m2']})",
           f"สีจริงผนังภายใน {PAINT['int']} 2 เที่ยว: {A.get('int', 0):.2f} ตร.ม. → {math.ceil(A.get('int', 0) / PAINT['wall_m2'] - 1e-9)} ถัง",
           f"สีรองพื้นฝ้า: {A.get('ceil_primer', 0):.2f} ตร.ม. → {math.ceil(A.get('ceil_primer', 0) / PAINT['ceil_m2'] - 1e-9)} ถัง (÷ {PAINT['ceil_m2']})",
           f"สีฝ้า 2 เที่ยว (ใน + ชายคา): {A.get('ceil', 0):.2f} ตร.ม. → {math.ceil(A.get('ceil', 0) / PAINT['ceil_m2'] - 1e-9)} ถัง",
           "ผนังห้องน้ำ (แบบ 3) และโคนผนังใต้ผิวพื้น: ไม่ทาสี (กระเบื้อง / ปูนกาว / ปูนทราย ST11 ปิด)"]
    return "\n".join(out)


# ---------------------------------------------------------------- ST10 selfcheck

def _check_paint(rows_before):
    def eq(a, b, what, rel=1e-4):
        assert abs(a - b) <= rel * max(abs(b), 1e-9), f"[{what}] model {a:.4f} != expected {b:.4f}"
    objs = {o.name: o for o in _coll(C_PAINT).objects}

    def boxes(name):
        if name not in objs:
            return []
        bm = _world_bm(objs[name])
        try:
            return _obj_boxes(bm, name)
        finally:
            bm.free()
    pr, c1e, c1i, c2 = boxes("PT_Primer"), boxes("PT_Coat1Ext"), boxes("PT_Coat1Int"), boxes("PT_Coat2")
    assert pr and c1e and c1i and c2, "[count] a paint layer is missing"
    assert "element" not in objs["PT_Coat2"].data, "[coat2] coat 2 carries a take-off row (coat 1 counts both coats)"
    plaster, covers, opens, boards = _paint_sources()
    pgrid = _Grid(plaster)
    cgrid = _Grid(covers)
    f, t = PAINT["film"], PAINT["film_t"]

    def thin_axis(b):
        d = [b[k + 3] - b[k] for k in range(3)]
        return d.index(min(d))

    def base_of(b, k):
        """Plaster face the film b sits on, exactly k films out; (piece, axis, sign) or None."""
        ax = thin_axis(b)
        if abs((b[ax + 3] - b[ax]) - t) > 2e-5:
            return None
        o = [i for i in range(3) if i != ax]
        for sg in (1, -1):
            pl = b[ax + 3] - k * f if sg > 0 else b[ax] + k * f
            probe = list(b)
            probe[ax], probe[ax + 3] = (pl - 1e-5, pl - 1e-6) if sg > 0 else (pl + 1e-6, pl + 1e-5)
            under = [q for q in pgrid.near(tuple(probe), 1e-5) if (abs(q[ax + 3] - pl) < 2e-5 if sg > 0 else abs(q[ax] - pl) < 2e-5)
                     and q[o[0]] - 1e-5 <= b[o[0]] and b[o[0] + 3] <= q[o[0] + 3] + 1e-5 and q[o[1]] - 1e-5 <= b[o[1]] and b[o[1] + 3] <= q[o[1] + 3] + 1e-5]
            if under:
                return under[0], ax, sg
        return None
    # direction: every film is k films out from a plaster face it lies wholly on (primer 1, coat 1 2, coat 2 3)
    for name, lst, k in (("primer", pr, 1), ("coat1", c1e + c1i, 2), ("coat2", c2, 3)):
        bad = [b for b in lst if base_of(b, k) is None]
        assert not bad, f"[{name}] {len(bad)} films not {k} × {f * 1000:.1f} mm off a plaster face: {tuple(round(v, 4) for v in bad[0])}"
    # nothing painted in front of a cover: each film's centre has no solid / board-above in front within reach
    for name, lst in (("primer", pr), ("coat1", c1e + c1i)):
        for b in lst:
            ax = thin_axis(b)
            c = [(b[k] + b[k + 3]) / 2 for k in range(3)]
            hit = [q for q in cgrid.near((c[0] - 1e-6, c[1] - 1e-6, c[2] - 1e-6, c[0] + 1e-6, c[1] + 1e-6, c[2] + 1e-6))
                   if all(q[k] + 1e-6 < c[k] < q[k + 3] - 1e-6 for k in range(3))]
            assert not hit, f"[{name}] a film inside a solid / behind a ceiling at {tuple(round(v, 3) for v in c)}"
    # coverage: every seen face sample point carries a primer film (probe the plaster faces independently, 0.25 m grid)
    prgrid = _Grid(pr)
    miss = 0
    tp, reach = PLASTER["t"], PAINT["reach"]
    for b in plaster:
        for ax, sg, pl, rect in _faces(b):
            if ax == 2:
                continue
            o = [i for i in range(3) if i != ax]
            n0 = max(1, int((rect[2] - rect[0]) / 0.25))
            n1 = max(1, int((rect[3] - rect[1]) / 0.25))
            for i in range(n0):
                for j in range(n1):
                    p = [0.0] * 3
                    p[o[0]] = rect[0] + (i + 0.5) * (rect[2] - rect[0]) / n0 + 1.3e-4
                    p[o[1]] = rect[1] + (j + 0.5) * (rect[3] - rect[1]) / n1 + 1.7e-4
                    front = list(p)
                    front[ax] = pl + sg * reach / 2
                    if any(all(q[k] < front[k] < q[k + 3] for k in range(3)) for q in cgrid.near((*front, *front), 1e-6)) or \
                       any(all(q[k] < front[k] < q[k + 3] for k in range(3)) for q in pgrid.near((*front, *front), 1e-6)):
                        continue                                  # covered: not seen
                    on = list(p)
                    on[ax] = pl + sg * (f - t / 2)
                    if not any(all(q[k] - 1e-6 <= on[k] <= q[k + 3] + 1e-6 for k in range(3)) for q in prgrid.near((*on, *on), 1e-5)):
                        miss += 1
    assert miss == 0, f"[primer] {miss} seen plaster sample points without primer"
    # coat 1 = primer (the tiles are covers: nothing under them); coat 2 = coat 1 one to one; ceilings = boards
    eq(_film_area(c1e + c1i), _film_area(pr), "coat1")
    assert len(c1e) + len(c1i) == len(pr), f"[coat1] {len(c1e) + len(c1i)} coat-1 films for {len(pr)} primer films"
    eq(_film_area(c2), _film_area(c1e + c1i), "coat2")
    assert len(c2) == len(c1e) + len(c1i), f"[coat2] {len(c2)} coat-2 films for {len(c1e) + len(c1i)} coat-1 films"
    cpr, cpa = boxes("PT_CeilPrimer"), boxes("PT_CeilPaint")
    ba = sum((b[3] - b[0]) * (b[4] - b[1]) for b in boards)
    eq(_film_area(cpr), ba, "ceilings")
    eq(_film_area(cpa), ba, "ceilings")
    for b in cpr + cpa:
        assert any(abs(q[2] - b[5] - (f - t)) < 2e-5 or abs(q[2] - b[5] - (2 * f - t)) < 2e-5 for q in boards if q[0] - 1e-6 <= b[0] and b[3] <= q[3] + 1e-6 and q[1] - 1e-6 <= b[1] and b[4] <= q[4] + 1e-6), \
            "[ceilings] a ceiling film not under its board"
    return f"ST10 ok: primer {_film_area(pr):.1f} m², coat 1 ext {_film_area(c1e):.1f} / int {_film_area(c1i):.1f} m², ceilings {ba:.1f} m²"
