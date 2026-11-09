"""KK01 ST08 มุงหลังคา – exec'd after kk01_roof.py (kk01_load.py).

Main roof: CPAC concrete tiles (Monier, as both BOQs price it; 33 × 42 cm, take-off 10.5 tiles/m² + 5 %, practice)
laid on the batten tops. Each roof plane's tile bed is an exact polygon: its own eave stretches plus the creases
(ridges, hips, valleys) it shares, chained into loops — so the bed areas add up to the plan inside the eave / cos θ.
Trims counted off the crease lengths (usual rules): ridge / hip caps 3.3 per m + 3 %, a three-way cap at every ridge
end, a two-way mid-ridge (Dry Tech), a round-end cap at every hip foot, a valley gutter along each valley.
Fascia: SCG 2in1 23.5 × 305 × 2.2 cm round the whole eave outline, outer face on the eave line, top at the batten
tops. Lean-to and canopy: metal sheet 0.3 mm + PU 1" on the purlins, 76 cm cover per sheet.
Objects: TL_<plane> (tile beds), FS_<n> (fascia), MS_<roof> (sheets). Spec: ST08_roof_cover_spec.md.
"""

TILE = dict(name="CPAC Monier 33×42 ซม.", per_m2=10.5, waste=0.05, t=0.03, cap_per_m=3.3, cap_waste=0.03)
FASCIA = dict(h=0.235, t=0.022, piece=3.05, name="เชิงชาย SCG 2in1 23.5×305×2.2 ซม.")
SHEET = dict(t=0.025, cover=0.76, name="เมทัลชีท 0.3 มม. + PU 1\"")
C_COVER = "KK01 ST08 Roof cover"
STAGES.append(C_COVER)


def _bed_z(dd):
    """Tile bed (batten tops) at inward distance dd."""
    return _z_top(dd) + _sec(ROOF["batten"])[1] / math.cos(math.radians(PITCH))


def _eave_segments(p):
    """Stretches of plane p's own eave line (grown-rect edges) where the roof just inside is p."""
    ax, k, dr = p
    e = k - dr * EAVE
    lo, hi = _plane_extent(p)
    f = lambda v: _on(p, *_xy(p, e + dr * 1e-4, v), 1e-6)
    return [(_xy(p, e, a), _xy(p, e, b)) for a, b in _intervals(f, lo, hi, 0.005) if b - a > 1e-3]


def _plane_loops():
    """plane -> [polygon [(x, y)...]] in plan: own eave stretches + creases of the plane, chained end to end."""
    lines = _lines()
    out = {}
    for p in _planes():
        segs = [(a, b) for a, b in _eave_segments(p)]
        segs += [(a, b) for kind, a, b, pl in lines if p in pl]
        if not segs:
            continue
        segs = [(tuple(a), tuple(b)) for a, b in segs]
        loops = []
        while segs:
            a, b = segs.pop(0)
            loop = [a, b]
            while True:
                end = loop[-1]
                i = next((i for i, (c, d) in enumerate(segs)
                          if math.dist(c, end) < 2e-3 or math.dist(d, end) < 2e-3), None)
                if i is None:
                    break
                c, d = segs.pop(i)
                loop.append(d if math.dist(c, end) < 2e-3 else c)
            assert math.dist(loop[0], loop[-1]) < 2e-3, f"tile bed of {p} does not close: {loop[0]} … {loop[-1]}"
            loops.append(loop[:-1])
        out[p] = loops
    return out


def _shoelace(poly):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))) / 2


def _outline_rects():
    return [(b[0] - EAVE, b[1] - EAVE, b[2] + EAVE, b[3] + EAVE) for b in HIP_BOXES.values()]


def _plan_area():
    """Exact plan area of the union of the eave rectangles (cell union)."""
    rs = _outline_rects()
    return _union_volume([(x0, y0, 0.0, x1, y1, 1.0) for x0, y0, x1, y1 in rs])


def _outline_edges():
    """Boundary of the union of the eave rectangles as axis-aligned segments (for the fascia)."""
    rs = _outline_rects()
    inside = lambda x, y: any(r[0] - 1e-9 < x < r[2] + 1e-9 and r[1] - 1e-9 < y < r[3] + 1e-9 for r in rs)
    xs = sorted({r[i] for r in rs for i in (0, 2)})
    ys = sorted({r[i] for r in rs for i in (1, 3)})
    edges = []
    for ax, coords, others in ((0, ys, xs), (1, xs, ys)):   # ax 0: edges along x at fixed y
        for c in coords:
            for a, b in zip(others, others[1:]):
                m = (a + b) / 2
                p_in = inside(m, c + 1e-4) if ax == 0 else inside(c + 1e-4, m)
                p_out = inside(m, c - 1e-4) if ax == 0 else inside(c - 1e-4, m)
                if p_in != p_out:
                    edges.append((ax, c, a, b, 1 if p_in else -1))   # +1: roof on the + side
    merged = []
    for e in sorted(edges):
        if merged and merged[-1][0] == e[0] and abs(merged[-1][1] - e[1]) < 1e-9 and abs(merged[-1][3] - e[2]) < 1e-9 and merged[-1][4] == e[4]:
            merged[-1] = (e[0], e[1], merged[-1][2], e[3], e[4])
        else:
            merged.append(e)
    return merged


def _cover_layout():
    t, c = _tan(), math.cos(math.radians(PITCH))
    beds = {}
    for p, loops in _plane_loops().items():
        beds[p] = loops
    # fascia boxes: outer face on the eave line, inner face at the fascia back, top at the bed level at the eave
    zt = _bed_z(-EAVE)
    fas = []
    for ax, k, a, b, side in _outline_edges():
        v0, v1 = sorted((k, k + side * FASCIA["t"]))
        fas.append(_box(ax, a, b, v0, v1, zt - FASCIA["h"], zt))
    fas = _disjoint(fas)
    sheets = {}
    for name, lr in LEAN_ROOFS.items():
        z0 = LEAN["top"] + _sec(LEAN["rafter"])[1] + _sec(LEAN["purlin"])[1]
        sheets[name] = (lr["x"][0], lr["y"][0], z0, lr["x"][1], lr["y"][1], z0 + SHEET["t"])
    return beds, fas, sheets


def build_roof_cover():
    c = _clear(C_COVER)
    tile_m = mat("M_CPAC_Tile", (0.45, 0.46, 0.48), 0.6)
    fas_m = mat("M_Fascia", (0.90, 0.89, 0.86), 0.7)
    sh_m = mat("M_MetalSheet", (0.55, 0.20, 0.15), 0.4, 0.6)
    beds, fas, sheets = _cover_layout()
    n = 0
    hb = _sec(ROOF["batten"])[1]
    for p, loops in beds.items():
        ax, k, dr = p
        name = f"TL_{'xy'[ax]}{k:g}{'+' if dr > 0 else '-'}"
        _drop(bpy.data.meshes, name)
        bm = bmesh.new()
        nrm = Vector(((-dr * math.sin(math.radians(PITCH))) if ax == 0 else 0,
                      (-dr * math.sin(math.radians(PITCH))) if ax == 1 else 0, math.cos(math.radians(PITCH))))
        for loop in loops:
            vs = [bm.verts.new((x, y, _bed_z(_d(p, x, y)))) for x, y in loop]
            top = [bm.verts.new(tuple(Vector(v.co) + nrm * TILE["t"])) for v in vs]
            bm.faces.new(vs[::-1])
            bm.faces.new(top)
            for i in range(len(vs)):
                j = (i + 1) % len(vs)
                bm.faces.new((vs[i], vs[j], top[j], top[i]))
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(tile_m)
        me["element"], me["type"], me["kind"], me["th"] = "tile_bed", "TILE", "tile", f"กระเบื้อง {TILE['name']}"
        me["plane"] = list(p)
        o = bpy.data.objects.new(name, me)
        c.objects.link(o)
        n += 1
    me = _boxes_data("FS_Fascia", fas, fas_m, element="fascia", type="FS", th=FASCIA["name"])
    c.objects.link(bpy.data.objects.new("FS_Fascia", me))
    for name, b in sheets.items():
        me = _box_data(f"MS_{name}", *b, sh_m, element="sheet", type=f"MS_{name}", th=f"{SHEET['name']} ({name})")
        c.objects.link(bpy.data.objects.new(f"MS_{name}", me))
    bpy.context.view_layer.update()
    return n


def _beds_read():
    """[(plane, plan area, sloped bed area, vertices)] read from the bed meshes (bottom faces)."""
    out = []
    for o in _coll(C_COVER).objects:
        me = o.data
        if not me or me.get("element") != "tile_bed":
            continue
        p = tuple(me["plane"])
        p = (int(p[0]), float(p[1]), int(p[2]))
        bm = _world_bm(o)
        bot = [f for f in bm.faces if f.normal.z < -0.8]
        plan = sum(_shoelace([(v.co.x, v.co.y) for v in f.verts]) for f in bot)
        slope = sum(f.calc_area() for f in bot)
        verts = [v.co.copy() for f in bot for v in f.verts]
        bm.free()
        out.append((p, plan, slope, verts, o.name))
    return out


def cover_report():
    beds = _beds_read()
    A = sum(b[2] for b in beds)
    tiles = math.ceil(A * TILE["per_m2"] * (1 + TILE["waste"]) / 10 - 1e-9) * 10
    lines = _lines()
    seg_len = lambda a, b, kind, pl: math.hypot(math.dist(a, b), _bed_z(_d(pl[0], *b)) - _bed_z(_d(pl[0], *a)))
    L = {k: sum(seg_len(a, b, k, pl) for kk, a, b, pl in lines if kk == k) for k in ("ridge", "hip", "valley")}
    caps = math.ceil((L["ridge"] + L["hip"]) * TILE["cap_per_m"] * (1 + TILE["cap_waste"]) - 1e-9)
    ridges = [l for l in lines if l[0] == "ridge"]
    feet = sum(1 for kk, a, b, pl in lines if kk == "hip" for q in (a, b) if _roof_d(*q) is None or _roof_d(*q) < -EAVE + 0.01)
    out = [f"กระเบื้อง {TILE['name']}: พื้นที่มุง {A:.2f} ตร.ม. (แปลน {sum(b[1] for b in beds):.2f} / cos {PITCH:g}°) "
           f"× {TILE['per_m2']} + {TILE['waste'] * 100:.0f} % → {tiles:,} แผ่น",
           f"แผ่นรองใต้กระเบื้อง / สะท้อนความร้อน ≈ {A:.2f} ตร.ม.",
           f"ครอบสัน {L['ridge']:.2f} ม. + ครอบตะเข้สัน {L['hip']:.2f} ม. → ครอบสันโค้ง {caps} แผ่น (3.3/ม. + 3 %)",
           f"ครอบโค้งสามทาง {2 * len(ridges)} ตัว · ครอบโค้งสองทาง (กลางสัน) {len(ridges)} ตัว · ครอบโค้งหางมน (ปลายตะเข้) {feet} ตัว",
           f"รางตะเข้ (ตะเข้ราง) {L['valley']:.2f} ม."]
    r = qto(C_COVER)
    fl = sum(max(b[3] - b[0], b[4] - b[1]) for b in r[("fascia", "FS")]["boxes"])
    out.append(f"{FASCIA['name']}: รอบชายคา {fl:.2f} ม. → {math.ceil(fl / FASCIA['piece'] * 1.05 - 1e-9)} แผ่น (เผื่อ 5 %)")
    for (el, tp), x in r.items():
        if el == "sheet":
            for b in x["boxes"]:
                w, l = b[3] - b[0], b[4] - b[1]
                out.append(f"{x['th']}: {w:.2f}×{l:.2f} = {w * l:.2f} ตร.ม. → {math.ceil(w / SHEET['cover'] - 1e-9)} แผ่น ยาว {l:.2f} ม.")
    paint = 0.0
    for o in _coll(C_ROOF).objects:
        if o.data and o.data.get("element") == "steel" and o.data["kind"] != "batten":
            bm = _world_bm(o)
            paint += sum(f.calc_area() for f in bm.faces)
            bm.free()
    out.append(f"ทาสีกันสนิมเหล็กรูปพรรณ (ไม่รวมระแนงกัลวาไนซ์): ผิวเหล็ก {paint:.2f} ตร.ม.")
    return "\n".join(out)


# ---------------------------------------------------------------- ST08 selfcheck

def _check_cover(rows_before):
    def eq(a, b, what, rel=1e-4):
        assert abs(a - b) <= rel * max(abs(b), 1e-9), f"[{what}] model {a:.4f} != expected {b:.4f}"
    beds = _beds_read()
    c = math.cos(math.radians(PITCH))
    want = {p for p in _planes() if _eave_segments(p)}          # every plane that reaches an eave is on the roof
    got_p = {b[0] for b in beds}
    assert got_p == want, f"[tiles] tiled planes {sorted(got_p)} != planes on the roof {sorted(want)}"
    plan = sum(b[1] for b in beds)
    eq(plan, _plan_area(), "tiles")                          # every bit of the plan inside the eave, once
    eq(sum(b[2] for b in beds), _plan_area() / c, "tiles")   # at the pitch
    hb = _sec(ROOF["batten"])[1]
    for p, pa, sa, verts, nm in beds:
        for v in verts:
            assert abs(v.z - _bed_z(_d(p, v.x, v.y))) < 1e-4, f"[tiles] {nm}: bed not on the batten tops at ({v.x:.2f}, {v.y:.2f})"
    # battens under every bed: some batten of ST07 lies on each plane
    bat = [m for m in _members() if m[1] == "batten"]
    for p, *_ in beds:
        assert any(_on(p, *((m[3] + m[4]) / 2).xy, 1e-6) for m in bat), f"[tiles] plane {p}: tiles with no battens under them"
    # fascia: round the whole outline, outer face on the eave line, top at the bed at the eave
    r = qto(C_COVER)
    fb = r.get(("fascia", "FS"), dict(boxes=[]))["boxes"]
    assert fb, "[fascia] no fascia"
    per = sum(b - a for ax, k, a, b, s in _outline_edges())
    got = sum(max(q[3] - q[0], q[4] - q[1]) for q in fb)
    assert abs(got - per) < 4 * FASCIA["t"] * 2 + 1e-6, f"[fascia] {got:.2f} m of fascia round a {per:.2f} m eave"
    zt = _bed_z(-EAVE)
    for q in fb:
        assert abs(q[5] - zt) < 1e-4 and abs(q[5] - q[2] - FASCIA["h"]) < 1e-4, f"[fascia] piece z {q[2]:.3f}..{q[5]:.3f}, bed at eave {zt:.3f}"
    for ax, k, a, b, s in _outline_edges():
        m = (a + b) / 2
        hit = [q for q in fb if (q[1] - 1e-6 <= k <= q[4] + 1e-6 and q[0] < m < q[3]) if ax == 0] if ax == 0 else \
            [q for q in fb if q[0] - 1e-6 <= k <= q[3] + 1e-6 and q[1] < m < q[4]]
        assert hit, f"[fascia] eave {'xy'[ax]}={k} at {m:.2f} has no fascia"
        q = hit[0]
        face = (q[1] if s > 0 else q[4]) if ax == 0 else (q[0] if s > 0 else q[3])
        assert abs(face - k) < 1e-5, f"[fascia] outer face {face:.3f} not on the eave line {k}"
        th = (q[4] - q[1]) if ax == 0 else (q[3] - q[0])
        assert abs(th - FASCIA_T) < 1e-5, f"[fascia] board {th * 100:.1f} cm thick; the rafters stop {FASCIA_T * 100:.1f} cm in"
    # rafters end at the fascia back
    feet = [m for m in _members() if m[1] == "rafter" and _roof_d(m[3].x, m[3].y) is not None
            and abs(_roof_d(m[3].x, m[3].y) - _eave_start()) < 1e-3]
    assert feet, "[fascia] no rafter ends at the fascia"
    for o, kind, sec, p0, p1, L in feet:   # the top corner of the square cut meets the board's back
        d = (p1 - p0).normalized()
        n = Vector((-d.x, -d.y, 0)).normalized() * (_sec(sec)[1] * math.sin(math.radians(PITCH)))
        tc = p0 + n
        assert abs(_roof_d(tc.x, tc.y) + EAVE - FASCIA["t"]) < 1e-3, f"[fascia] {o.name}: top corner {_roof_d(tc.x, tc.y):.3f} not at the board"
    for o, kind, sec, p0, p1, L in _members():   # no steel inside the fascia board
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        lo = [min(v[i] for v in vs) for i in range(3)]
        hi = [max(v[i] for v in vs) for i in range(3)]
        near = [q for q in fb if q[0] < hi[0] and q[3] > lo[0] and q[1] < hi[1] and q[4] > lo[1] and q[2] < hi[2] and q[5] > lo[2]]
        if not near:
            continue
        box = obb(vs, (p1 - p0).normalized())
        for q in near:
            c = Vector(((q[0] + q[3]) / 2, (q[1] + q[4]) / 2, (q[2] + q[5]) / 2))
            qb = (c, [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))], [(q[3] - q[0]) / 2, (q[4] - q[1]) / 2, (q[5] - q[2]) / 2])
            assert obb_overlap(box, qb) <= 2e-3, f"[fascia] {o.name} runs into the fascia board"
    # sheets on the purlins, covering each lean-to / canopy frame
    pur = [m for m in _members() if m[1] == "purlin"]
    sb = [b for (el, _), x in r.items() if el == "sheet" for b in x["boxes"]]
    assert len(sb) == len(LEAN_ROOFS), f"[sheet] {len(sb)} sheet roofs, {len(LEAN_ROOFS)} frames"
    for name, lr in LEAN_ROOFS.items():
        q = [b for b in sb if abs(b[0] - lr["x"][0]) < 1e-5 and abs(b[1] - lr["y"][0]) < 1e-5]
        assert q and abs(q[0][3] - lr["x"][1]) < 1e-5 and abs(q[0][4] - lr["y"][1]) < 1e-5, f"[sheet] {name}: sheet not over the frame"
        ptop = max(m[3].z + _sec(m[2])[1] for m in pur if lr["x"][0] - 1e-6 <= m[3].x <= lr["x"][1] + 1e-6 and lr["y"][0] - 0.1 <= m[3].y <= lr["y"][1] + 0.1)
        assert abs(q[0][2] - ptop) < 1e-5, f"[sheet] {name}: sheet at {q[0][2]:.3f}, purlin tops {ptop:.3f}"
    return f"ST08 ok: {len(beds)} tiled planes {sum(b[2] for b in beds):.2f} m², fascia {got:.2f} m, {len(sb)} sheet roofs"
