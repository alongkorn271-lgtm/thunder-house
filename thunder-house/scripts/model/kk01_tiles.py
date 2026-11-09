"""KK01 ST11 กระเบื้องพื้น + ผนังห้องน้ำ (generic ST11) – exec'd after kk01_paint.py; BUILT BEFORE ST10 paint (the paint
stops where the finishes are, as common practice's E42 rebuild walls → tiles → primer → coats). Site order: bath
waterproofing → screed → adhesive + tiles + grout, after coat 1 of the walls.

A-04 levels are finished floors (user, 5 พ.ย. 69): FL2 +0.80 on the topping +0.77, FL3 / FL4 +0.70 on slab / beam tops
+0.67 — 3 cm = screed + adhesive + tile. A-02 floors: FL2 กระเบื้องผิวมัน 60×60 (rooms), FL3 ผิวหยาบ 60×60 (verandahs,
laundry), FL4 ผิวหยาบ 40×40 (baths, A-04 tags); wall type 3 กระเบื้องเคลือบ 8"×10" in both baths to the ceiling (A-13).
The floor plan is read from the structure: the topping footprint → FL2, the S panels to the beams' outer faces off the
topping → FL3 / FL4, less every brick / tie / plaster / column standing in the finish height. Grids: one FL2 grid for
the whole house through the door thresholds (centred on the living room), one per verandah / bath, joint or tile on the
centre whichever leaves the bigger edge cut (practice). Where FL2 meets a +0.70 floor (doors D1, D2, D3, D4) a riser tile
on its bed stands in front of the topping edge and the upper tile reaches over it. Bath walls: tiles from the floor
bed's underside to the ceiling on every seen plaster face in the bath (reveals stay for the frames, ST14); one row origin
per bath (its floor), inside corners: faces along x run through, faces along y stop at their tiles. Waterproofing
(practice): the bath floor, walls 0.30 up, 1.80 in the shower (A-13: the 0.85 m bay by W5; bath 2 the same at its W5,
assumed); fibreglass mesh along the floor–wall and wall–wall corners it covers.
Counts off the layout (every cell a tile touches = 1, two cut pieces ≤ 45 % share one) + 3 %, then whole boxes; risers
from strips cut out of the lower floor's tiles. Not done: steps (A-04 front / rear / laundry), floor falls 1:100 to
the drains, skirting (A-02 has none), PVC trims on the tiles' outside corners, the shower partition in the baths.
Objects (collection "KK01 ST11 Tiles"): FT_<zone>_{Tiles,Grout,Bed,Screed}, FT_Risers, FT_RiserBed, FT_Wall_Tiles,
FT_Wall_Bed, FT_Waterproof. Spec: ST11_tiles_spec.md.
"""

FT = dict(
    FL2=dict(size=(0.60, 0.60, 0.009), joint=0.002, bed=0.005, box=4, level=FL2,
             th="กระเบื้องพื้นผิวมัน 60×60 ซม. (FL2 ห้องทั่วไป)", rgb=(0.88, 0.86, 0.82)),
    FL3=dict(size=(0.60, 0.60, 0.009), joint=0.003, bed=0.005, box=4, level=FL_WET,
             th="กระเบื้องพื้นผิวหยาบ 60×60 ซม. (FL3 ระเบียง / ซักล้าง)", rgb=(0.56, 0.53, 0.49)),
    FL4=dict(size=(0.40, 0.40, 0.008), joint=0.003, bed=0.005, box=6, level=FL_WET,
             th="กระเบื้องพื้นผิวหยาบ 40×40 ซม. (FL4 ห้องน้ำ)", rgb=(0.64, 0.64, 0.62)),
    W3=dict(size=(0.20, 0.25, 0.007), joint=0.002, bed=0.004, box=20,
            th='กระเบื้องเคลือบบุผนัง 8"×10" (20×25 ซม. แนวตั้ง, ผนังแบบ 3 ห้องน้ำถึงฝ้า)', rgb=(0.93, 0.94, 0.93)))
TILED_ROOMS = ("bath1", "bath2")                     # wall type 3 (A-13): tiled to the ceiling
FLOOR_ZONES = dict(house="FL2", verandah_front="FL3", rear="FL3", bath1="FL4", bath2="FL4")
SPARE = 0.03                                         # breakage over the layout count (practice)
ADH = dict(th="ปูนกาวซีเมนต์ปูกระเบื้อง 20 กก.", big=2.5, small=5.5)   # m² a bag: notch 10×10 (tile ≥ 40 cm) / 6×6
GROUT = dict(th="ยาแนว 1 กก.", rho=1.6, waste=0.10)                   # kg = A·(L+W)/(L·W)·j·t·ρ (mm), practice
WP = dict(th="กันซึมชนิดยืดหยุ่น 2 เที่ยว (ซีเมนต์ทากันซึม 20 กก.)", t=0.0015, kg=1.5, bag=20.0, up=0.30, shower=1.80,
          mesh="ไฟเบอร์เมชเสริมมุม กว้าง 20 ซม. ม้วน 10 ม.", roll=10.0)
SHOWER = dict(bath1=(-1.0, 0.85), bath2=(12.15, 14.0))   # x range of the shower bay (A-13 0.85 by W5; bath 2 assumed)
SCREED = dict(th="ปูนทราย 1:3 ปรับระดับใต้กระเบื้อง")
# Steps (A-04, read at 1:100; user: "ทำบันไดต่อ"): 3 treads + 4 equal risers FL3 +0.70 → GL, against the slab edge (the
# beam's outer face); (normal axis, edge plane, outward sign), span between the column plaster faces, treads (front 0.30
# as drawn, rear / laundry 0.25 as drawn). RC on 5 cm sand, base −0.10, wire mesh 4 mm @0.20 (practice E42; assumed),
# FL3 tile on the treads and risers, each tread tile reaching over the riser below it, the verandah tile over riser 1.
STEPS = dict(rise=4, base=-0.10, sand=0.05, mesh_d=0.004, mesh_s=0.20, mesh_z=0.04, mesh_cover=0.05, grade="St.240 ksc",
             flights=dict(front=dict(edge=(1, -0.10, -1), span=(5.115, 7.13), treads=(0.30, 0.30, 0.30), zone="verandah_front"),
                          rear=dict(edge=(0, 3.40, -1), span=(7.615, 9.085), treads=(0.25, 0.25, 0.25), zone="rear"),
                          laundry=dict(edge=(0, 10.60, 1), span=(11.30, 12.30), treads=(0.25, 0.25, 0.25), zone="rear")))
C_TILE = "KK01 ST11 Tiles"
STAGES.append(C_TILE)


def _clip_minus(rects, cuts):
    """2D rects (x0, y0, x1, y1) less the cut rects, cutting only by the cuts that overlap."""
    out = []
    for r in rects:
        near = [c for c in cuts if c[0] < r[2] - 1e-9 and c[2] > r[0] + 1e-9 and c[1] < r[3] - 1e-9 and c[3] > r[1] + 1e-9]
        out += _rects_minus([r], near) if near else [r]
    return out


def _disjoint2(rects):
    out = []
    for r in rects:
        out += _clip_minus([r], out)
    return out


def _floor_obstacles(z0, z1):
    """Plan rects of everything standing in the finish height z0..z1 (brick, ties, plaster, columns)."""
    return [(b[0], b[1], b[3], b[4]) for b in _obstacles() if b[2] < z1 - 1e-6 and b[5] > z0 + 1e-6]


def _floor_zones():
    """{zone: (tile type, finished level, structure top, [plan rects])} (see module doc)."""
    w = GBEAM["b"] / 2
    house = [(b[0], b[1], b[3], b[4]) for b in _footprint()]
    wet = _clip_minus(_disjoint2([(r[0] - w, r[1] - w, r[2] + w, r[3] + w) for _, k, r in _panels() if k == "S"]), house)
    house = _clip_minus(house, _floor_obstacles(TOPPING["top"], FL2))
    wet = _clip_minus(wet, _floor_obstacles(GB_TOP, FL_WET))
    obst = _obstacles()
    baths = {n: _room_rect(s, 1.5, obst) for n, s, *_ in ROOMS if n in TILED_ROOMS}
    zones = {z: [] for z in FLOOR_ZONES}
    zones["house"] = house
    for q in wet:
        c = ((q[0] + q[2]) / 2, (q[1] + q[3]) / 2)
        b = next((n for n, r in baths.items() if r[0] - 0.08 <= c[0] <= r[2] + 0.08 and r[1] - 0.08 <= c[1] <= r[3] + 0.08), None)
        zones[b or ("verandah_front" if c[1] < 2.0 else "rear")].append(q)
    return {z: (FLOOR_ZONES[z], FT[FLOOR_ZONES[z]]["level"], FL2 - FINISH if z == "house" else GB_TOP, rs) for z, rs in zones.items()}


def _risers(zones):
    """Level changes FL2 → +0.70 inside the plan: [(lower zone, ax, plane, lo, hi, sg)] — the topping edge at `plane`
    (normal along ax), the lower floor on the +sg side, along lo..hi."""
    out = []
    for z, (tp, lvl, st, rs) in zones.items():
        if z == "house":
            continue
        for h in zones["house"][3]:
            for q in rs:
                for ax in (0, 1):
                    o = 1 - ax
                    lo, hi = max(h[o], q[o]), min(h[o + 2], q[o + 2])
                    if hi - lo < 1e-4:
                        continue
                    if abs(h[ax + 2] - q[ax]) < 1e-6:
                        out.append((z, ax, h[ax + 2], lo, hi, 1))
                    elif abs(h[ax] - q[ax + 2]) < 1e-6:
                        out.append((z, ax, h[ax], lo, hi, -1))
    return out


def _strip(ax, plane, lo, hi, sg, d0, d1, z0, z1):
    """Box beside a vertical plane (normal ax) from d0 to d1 out on the +sg side, along lo..hi."""
    a, b = sorted((plane + sg * d0, plane + sg * d1))
    return (a, lo, z0, b, hi, z1) if ax == 0 else (lo, a, z0, hi, b, z1)


def _origin(lo, hi, a, jw):
    """Grid start along one axis so [lo, hi] has equal cuts at both ends: a joint or a tile on the centre, whichever
    leaves the bigger edge cut (practice)."""
    best = None
    for mid_joint in (True, False):
        c = (lo + hi) / 2
        o = c + jw / 2 if mid_joint else c - a / 2
        o0 = o - (math.floor((o - lo) / (a + jw)) + 1) * (a + jw)
        edge = (o0 + a + jw) - lo
        edge = edge if edge > 1e-6 else edge + a + jw
        if best is None or edge > best[0]:
            best = (edge, o0)
    return best[1]


def _cells(region, o, a, b, jw):
    """Layout of a × b tiles from origin o with joints jw over the region rects: {(i, j): [pieces (u0, v0, u1, v1)]}."""
    u0, v0 = min(r[0] for r in region), min(r[1] for r in region)
    u1, v1 = max(r[2] for r in region), max(r[3] for r in region)
    pa, pb = a + jw, b + jw
    cells = {}
    for i in range(math.floor((u0 - o[0]) / pa) - 1, math.ceil((u1 - o[0]) / pa) + 1):
        for j in range(math.floor((v0 - o[1]) / pb) - 1, math.ceil((v1 - o[1]) / pb) + 1):
            cr = (o[0] + i * pa, o[1] + j * pb, o[0] + i * pa + a, o[1] + j * pb + b)
            for r in region:
                q = (max(cr[0], r[0]), max(cr[1], r[1]), min(cr[2], r[2]), min(cr[3], r[3]))
                if q[2] - q[0] > 1e-5 and q[3] - q[1] > 1e-5:
                    cells.setdefault((i, j), []).append(q)
    return cells


def _joints(region, o, a, b, jw):
    """Joint strips of a layout inside the region (the strips across u give way at the crossings)."""
    u0, v0 = min(r[0] for r in region), min(r[1] for r in region)
    u1, v1 = max(r[2] for r in region), max(r[3] for r in region)
    us, vs = [], []
    for ax, (lo, hi, oo, p) in enumerate(((u0, u1, o[0], a + jw), (v0, v1, o[1], b + jw))):
        k = math.floor((lo - oo) / p)
        while oo + k * p - jw < hi:
            g0 = oo + k * p - jw
            for r in region:
                s = (max(g0, r[0]), r[1], min(g0 + jw, r[2]), r[3]) if ax == 0 else (r[0], max(g0, r[1]), r[2], min(g0 + jw, r[3]))
                if s[2] - s[0] > 1e-6 and s[3] - s[1] > 1e-6:
                    (us if ax == 0 else vs).append(s)
            k += 1
    return us + _clip_minus(vs, us)


def _count(cells, a, b):
    """(whole, tiles for the cut pieces): a cell covered to its full size is whole; two cuts of ≤ 45 % share a tile."""
    areas = [sum((p[2] - p[0]) * (p[3] - p[1]) for p in ps) for ps in cells.values()]
    whole = sum(1 for x in areas if abs(x - a * b) < 1e-6)
    small = sum(1 for x in areas if x <= 0.45 * a * b + 1e-9)
    return whole, len(areas) - whole - small + math.ceil(small / 2)


def _grout_kg(area, a, b, jw, t):
    L, W = a * 1000, b * 1000
    return area * (L + W) / (L * W) * jw * 1000 * t * 1000 * GROUT["rho"]


def _bath_faces():
    """{bath: [(ax, sg, plane, [rects (u0, z0, u1, z1)])]} seen plaster faces looking into the bath (vertical only)."""
    rooms = _ceiling_rooms()
    out = {b: {} for b in TILED_ROOMS}
    _tile_cover[0] = False
    try:
        seen = _seen_faces()
    finally:
        _tile_cover[0] = True
    for ax, sg, pl, pcs in seen:
        if ax == 2:
            continue
        for p in pcs:
            room = _room_of_face(ax, sg, pl, p, rooms)
            if room in TILED_ROOMS:
                out[room].setdefault((ax, sg, round(pl, 6)), []).append(p)
    return {b: [(k[0], k[1], k[2], v) for k, v in sorted(d.items(), key=lambda kv: (-kv[0][0], kv[0][2]))] for b, d in out.items()}


def _face_box(ax, sg, pl, p, d0, d1):
    """3D box over face rect p (u along the other horizontal axis, z) from d0 to d1 off the plane."""
    a, b = sorted((pl + sg * d0, pl + sg * d1))
    return (a, p[0], p[1], b, p[2], p[3]) if ax == 0 else (p[0], a, p[1], p[2], b, p[3])


def _proj(ax, box):
    """A 3D box as a face rect (u, z) for a face of normal ax."""
    return (box[1], box[2], box[4], box[5]) if ax == 0 else (box[0], box[2], box[3], box[5])


def _step_geom(nm):
    """(flight, ax, E, sg, eps, rise, finished levels h[0..n+1] (h[0] = FL3, last = GL), tread fronts c[0..n] from E)."""
    f = STEPS["flights"][nm]
    ax, E, sg = f["edge"]
    t = FT["FL3"]
    eps = t["bed"] + t["size"][2]
    r = (FL_WET - GL) / STEPS["rise"]
    h = [FL_WET - i * r for i in range(STEPS["rise"] + 1)]
    c = [0.0]
    for tr in f["treads"]:
        c.append(c[-1] + tr)
    return f, ax, E, sg, eps, r, h, c


def _steps_layout():
    """RC steps, sand, excavation, mesh, tread + riser tiles (+ beds); the verandah's strip over riser 1."""
    out = dict(conc=[], sand=[], exc=[], mesh=[], tread=[], tread_bed=[], riser=[], riser_bed=[], grow={}, area=0.0, strips=0)
    pads = [b for (el, _), x in qto(C_GB).items() if el in ("lean_concrete", "sand") for b in x["boxes"]]
    t = FT["FL3"]
    a, _, tt = t["size"]
    for nm in STEPS["flights"]:
        f, ax, E, sg, eps, r, h, c = _step_geom(nm)
        lo, hi = f["span"]
        S = lambda d0, d1, z0, z1: _strip(ax, E, lo, hi, sg, d0, d1, z0, z1)
        n = len(f["treads"])
        assert n == STEPS["rise"] - 1, f"steps {nm}: {n} treads for {STEPS['rise']} risers"
        for i in range(1, n + 1):                       # tread i: its concrete, bed, tile (over riser i + 1's top)
            zb = h[i + 1] - eps if i < n else STEPS["base"]
            out["conc"] += [q for q in _cut(S(0.0, c[i], zb, h[i] - eps), pads) if min(q[3] - q[0], q[4] - q[1], q[5] - q[2]) > 1e-6]
            out["tread_bed"].append(S(c[i - 1], c[i] + eps, h[i] - eps, h[i] - tt))
            out["tread"].append(S(c[i - 1], c[i] + eps, h[i] - tt, h[i]))
            out["area"] += (hi - lo) * (c[i] + eps - c[i - 1])
            out["strips"] += math.ceil((hi - lo) / a) * math.ceil((c[i] + eps - c[i - 1]) / a)
        for i in range(1, n + 2):                       # riser i on tread i (the last on the ground), up to under the bed above
            z0, z1 = (h[i] if i <= n else GL), h[i - 1] - eps
            out["riser_bed"].append(S(c[i - 1], c[i - 1] + t["bed"], z0, z1))
            out["riser"].append(S(c[i - 1] + t["bed"], c[i - 1] + eps, z0, z1))
            out["area"] += (hi - lo) * (z1 - z0)
            out["strips"] += math.ceil(math.ceil((hi - lo) / a) / max(1, math.floor(a / (z1 - z0 + t["joint"]))))
        g = S(0.0, eps, 0.0, 1.0)
        out["grow"].setdefault(f["zone"], []).append((g[0], g[1], g[3], g[4]))
        out["sand"].append(S(0.0, c[n], STEPS["base"] - STEPS["sand"], STEPS["base"]))
        out["exc"].append(S(0.0, c[n] + eps, STEPS["base"] - STEPS["sand"], GL))
        mc = STEPS["mesh_cover"]
        m = S(mc, c[n] - mc, 0.0, 1.0)
        m = (m[0] + (mc if ax == 1 else 0.0), m[1] + (mc if ax == 0 else 0.0), 0.0,
             m[3] - (mc if ax == 1 else 0.0), m[4] - (mc if ax == 0 else 0.0), 1.0)
        out["mesh"] += _mesh_wires([m], STEPS["mesh_s"], STEPS["base"] + STEPS["mesh_z"])
    return out


def _tiles_layout():
    """Every finish box of the stage + the take-off tallies."""
    zones = _floor_zones()
    risers = _risers(zones)
    L = dict(tiles={}, grout={}, bed={}, screed={}, riser=[], riser_bed=[], wall=[], wall_bed=[], wp=[], tally={},
             zones=zones, risers=risers, mesh=0.0)
    tally = {k: dict(area=0.0, whole=0, cut=0, strips=0) for k in FT}
    up = FT["FL2"]
    L["steps"] = st = _steps_layout()
    tally["FL3"]["area"] += st["area"]
    tally["FL3"]["strips"] += st["strips"]
    # risers: on the lower floor's screed, up to under the FL2 tile's bed; the FL2 tile + bed reach over them
    grow, shrink = {z: list(v) for z, v in st["grow"].items()}, {}
    for z, ax, pl, lo, hi, sg in risers:
        tp = FT[zones[z][0]]
        a, _, t = tp["size"]
        d = tp["bed"] + t
        zb, ztop = FL_WET - t - tp["bed"], FL2 - up["size"][2] - up["bed"]
        L["riser_bed"].append(_strip(ax, pl, lo, hi, sg, 0.0, tp["bed"], zb, ztop))
        L["riser"].append(_strip(ax, pl, lo, hi, sg, tp["bed"], d, zb, ztop))
        s = _strip(ax, pl, lo, hi, sg, 0.0, d, 0.0, 1.0)
        grow.setdefault("house", []).append((s[0], s[1], s[3], s[4]))
        shrink.setdefault(z, []).append((s[0], s[1], s[3], s[4]))
        h = ztop - zb
        tally[zones[z][0]]["area"] += h * (hi - lo)
        tally[zones[z][0]]["strips"] += math.ceil(math.ceil((hi - lo) / a) / max(1, math.floor(a / (h + tp["joint"]))))
    # bath walls: waterproofing, bed, tiles
    w3 = FT["W3"]
    wa, wbh, wt = w3["size"]
    wb = w3["bed"] + wt
    faces = _bath_faces()
    wall_env = []                                   # plan footprints of the wall tiles (+ bed), cut out of the bath floors
    for bath, fl in faces.items():
        f4 = FT["FL4"]
        z_lo = FL_WET - f4["size"][2] - f4["bed"]
        sx = SHOWER[bath]
        placed_env, placed_wp, corners = [], [], {}
        for ax, sg, pl, pcs in fl:              # ax 1 (faces along x) first: they run through the inside corners
            rects = [(p[0], max(p[1], GB_TOP), p[2], p[3]) for p in pcs if p[3] > z_lo + 1e-6]
            env_cut = [_proj(ax, i) for e in placed_env if (i := _inter(_face_box(ax, sg, pl, (-99, -99, 99, 99), 0.0, wb), e))
                       and min(i[k + 3] - i[k] for k in range(3)) > 1e-7]
            wp_cut = [_proj(ax, i) for e in placed_wp + placed_env if (i := _inter(_face_box(ax, sg, pl, (-99, -99, 99, 99), 0.0, WP["t"]), e))
                      and min(i[k + 3] - i[k] for k in range(3)) > 1e-7]
            tile_r = _clip_minus([(r[0], max(r[1], z_lo), r[2], r[3]) for r in rects], env_cut)
            # waterproofing up the face: 0.30, 1.80 in the shower bay (split at the bay's x ends on faces along x)
            for r in _clip_minus([(r[0], max(r[1], GB_TOP + WP["t"]), r[2], r[3]) for r in rects], wp_cut):
                cuts = sorted({r[0], r[2], *(c for c in sx if r[0] < c < r[2])}) if ax == 1 else [r[0], r[2]]
                for u0, u1 in zip(cuts, cuts[1:]):
                    xm = (u0 + u1) / 2 if ax == 1 else pl
                    h = FL_WET + (WP["shower"] if sx[0] <= xm <= sx[1] else WP["up"])
                    if h > r[1] + 1e-6:
                        b = _face_box(ax, sg, pl, (u0, r[1], u1, min(h, r[3])), 0.0, WP["t"])
                        L["wp"].append(b)
                        placed_wp.append(b)
                        for u in (u0, u1):
                            corners[(ax, round(u, 4))] = max(corners.get((ax, round(u, 4)), 0.0), min(h, r[3]) - GB_TOP)
            if not tile_r:
                continue
            for r in tile_r:
                bed = _face_box(ax, sg, pl, r, 0.0, w3["bed"])
                L["wall_bed"] += [q for q in _cut(bed, L["wp"]) if min(q[3] - q[0], q[4] - q[1], q[5] - q[2]) > 1e-6]
                e = _face_box(ax, sg, pl, r, 0.0, wb)
                placed_env.append(e)
                wall_env.append((e[0], e[1], e[3], e[4]))
            o = (min(r[0] for r in tile_r), z_lo)
            cells = _cells(tile_r, o, wa, wbh, w3["joint"])
            w_, c_ = _count(cells, wa, wbh)
            tally["W3"]["whole"] += w_
            tally["W3"]["cut"] += c_
            for ps in cells.values():
                for p in ps:
                    L["wall"].append(_face_box(ax, sg, pl, p, w3["bed"], wb))
                    tally["W3"]["area"] += (p[2] - p[0]) * (p[3] - p[1])
            tally["W3"]["area"] += sum((r[2] - r[0]) * (r[3] - r[1]) for r in tile_r) - sum(
                (p[2] - p[0]) * (p[3] - p[1]) for ps in cells.values() for p in ps)   # + the joints: area by the face
        # fibreglass mesh: the floor–wall corner round the bath, the wall–wall corners up to the coat height
        L["mesh"] += sum(r[2] - r[0] for ax, sg, pl, pcs in fl for r in pcs if r[1] <= z_lo + 1e-6)
        ends = {}
        for ax, sg, pl, pcs in fl:
            for r in pcs:
                for u in (r[0], r[2]):
                    ends.setdefault((round(u, 4) if ax == 1 else round(pl, 4), round(pl, 4) if ax == 1 else round(u, 4)), set()).add(ax)
        L["mesh"] += sum(WP["shower"] if SHOWER[bath][0] <= p[0] <= SHOWER[bath][1] else WP["up"] for p, s in ends.items() if s == {0, 1})
    # floors
    for z, (tp, lvl, st, rs) in zones.items():
        if not rs:
            continue
        f = FT[tp]
        a, b, t = f["size"]
        jw = f["joint"]
        region = _clip_minus(rs, shrink.get(z, []))
        under = list(region)                                      # screed: the whole floor less the risers
        if z in TILED_ROOMS:
            region = _clip_minus(region, wall_env)
        region = region + grow.get(z, [])
        if z in TILED_ROOMS:
            L["wp"] += [(q[0], q[1], st, q[2], q[3], st + WP["t"]) for q in _clip_minus(rs, [])]
        bx0, by0 = min(q[0] for q in rs), min(q[1] for q in rs)
        bx1, by1 = max(q[2] for q in rs), max(q[3] for q in rs)
        if z == "house":
            lv = _room_rect(next(s for n, s, *_ in ROOMS if n == "living"), 1.5, _obstacles())
            bx0, by0, bx1, by1 = lv
        o = (_origin(bx0, bx1, a, jw), _origin(by0, by1, b, jw))
        cells = _cells(region, o, a, b, jw)
        w_, c_ = _count(cells, a, b)
        tally[tp]["whole"] += w_
        tally[tp]["cut"] += c_
        L["tiles"][z] = [(p[0], p[1], lvl - t, p[2], p[3], lvl) for ps in cells.values() for p in ps]
        L["grout"][z] = [(s[0], s[1], lvl - t, s[2], s[3], lvl) for s in _joints(region, o, a, b, jw)]
        tally[tp]["area"] += sum((q[2] - q[0]) * (q[3] - q[1]) for q in region)
        L["bed"][z] = [(q[0], q[1], lvl - t - f["bed"], q[2], q[3], lvl - t) for q in region]
        s0 = st + (WP["t"] if z in TILED_ROOMS else 0.0)
        sc = [(q[0], q[1], s0, q[2], q[3], lvl - t - f["bed"]) for q in under]
        L["screed"][z] = [p for q in sc for p in _cut(q, L["wp"]) if min(p[3] - p[0], p[4] - p[1], p[5] - p[2]) > 1e-6]
    L["tally"] = tally
    return L


def build_tiles():
    """ST11: floors, risers, bath walls, waterproofing; take-off props on the objects."""
    c = _clear(C_TILE)
    L = _tiles_layout()
    mats = {k: mat(f"M_Tile_{k}", v["rgb"], 0.15 if k in ("FL2", "W3") else 0.6) for k, v in FT.items()}
    grout_m = mat("M_Grout", (0.72, 0.72, 0.70), 0.8)
    adh_m = mat("M_TileAdhesive", (0.62, 0.62, 0.60), 0.9)
    scr_m = mat("M_Screed", (0.55, 0.54, 0.50), 0.95)
    wp_m = mat("M_Waterproof", (0.30, 0.45, 0.62), 0.7)

    def put(name, boxes, m, **props):
        if boxes:
            c.objects.link(bpy.data.objects.new(name, _boxes_data(name, boxes, m, **props)))
    for z, (tp, lvl, st, rs) in L["zones"].items():
        if not L["tiles"].get(z):
            continue
        f = FT[tp]
        put(f"FT_{z}_Tiles", L["tiles"][z], mats[tp], element="floor_tile", type=tp, th=f["th"], level=lvl, zone=z)
        put(f"FT_{z}_Grout", L["grout"][z], grout_m, element="grout", type=tp, th=GROUT["th"])
        put(f"FT_{z}_Bed", L["bed"][z], adh_m, element="adhesive", type=tp, th=ADH["th"])
        put(f"FT_{z}_Screed", L["screed"][z], scr_m, element="screed", type="SC", th=SCREED["th"])
    put("FT_Risers", L["riser"], mats["FL3"], element="riser_tile", type="RS", th="กระเบื้องลูกตั้งต่างระดับ (ตัดจากกระเบื้องพื้นชั้นล่าง)")
    put("FT_RiserBed", L["riser_bed"], adh_m, element="adhesive", type="RS", th=ADH["th"])
    put("FT_Wall_Tiles", L["wall"], mats["W3"], element="wall_tile", type="W3", th=FT["W3"]["th"])
    put("FT_Wall_Bed", L["wall_bed"], adh_m, element="adhesive", type="W3", th=ADH["th"])
    put("FT_Waterproof", L["wp"], wp_m, element="membrane", type="WP", th=WP["th"])
    st = L["steps"]
    conc = mat("M_Concrete", (0.50, 0.50, 0.48), 0.85)
    sand = mat("M_Sand", (0.76, 0.68, 0.52), 0.95)
    steel = mat("M_Rebar", (0.28, 0.17, 0.11), 0.55, 0.6)
    put("FT_Step_Conc", st["conc"], conc, element="concrete", type="STEP", grade=STEPS["grade"], th="คอนกรีตบันได ค.ส.ล. (บนทรายอัดแน่น)")
    put("FT_Step_Sand", st["sand"], sand, element="sand", type="STEP", th=f"ทรายหยาบอัดแน่นรองบันได {STEPS['sand'] * 100:.0f} ซม.")
    put("FT_Step_Treads", st["tread"], mats["FL3"], element="step_tile", type="FL3", th="กระเบื้อง FL3 ลูกนอนบันได")
    put("FT_Step_TreadBed", st["tread_bed"], adh_m, element="adhesive", type="STEP", th=ADH["th"])
    put("FT_Step_Risers", st["riser"], mats["FL3"], element="step_tile", type="FL3R", th="กระเบื้อง FL3 ลูกตั้งบันได")
    put("FT_Step_RiserBed", st["riser_bed"], adh_m, element="adhesive", type="STEPR", th=ADH["th"])
    ex = bpy.data.objects.new("FT_Step_Exc", _boxes_data("FT_Step_Exc", st["exc"], None, element="excavation", type="STEP", th="ขุดดินบันได"))
    ex.hide_viewport = ex.hide_render = True
    c.objects.link(ex)
    c.objects.link(bpy.data.objects.new("FT_Step_Mesh", _rebar_data("FT_Step_Mesh", st["mesh"], STEPS["mesh_d"], steel, element="mesh",
                   type="STEP", th="ไวร์เมชบันได 4 มม. @0.20", bar="Wire mesh 4 mm @0.20", dia_mm=4, spacing=STEPS["mesh_s"])))
    tq = bpy.data.objects.new("FT_Qty", None)                    # the take-off tallies (an empty: no geometry)
    for k, x in L["tally"].items():
        a, b, t = FT[k]["size"]
        tq[f"{k}_area"], tq[f"{k}_whole"], tq[f"{k}_cut"], tq[f"{k}_strips"] = x["area"], x["whole"], x["cut"], x["strips"]
        tq[f"{k}_need"] = math.ceil((x["whole"] + x["cut"] + x["strips"]) * (1 + SPARE) - 1e-9)
    tq["mesh"] = L["mesh"]
    c.objects.link(tq)
    bpy.context.view_layer.update()
    return sum(len(v) for v in L["tiles"].values())


def _ft_boxes(prefix=""):
    """{object name: boxes} of the stage (meshes only)."""
    out = {}
    for o in _coll(C_TILE).objects:
        if o.type == "MESH" and o.name.startswith(prefix) and o.data.get("element") not in ("excavation", "mesh"):
            bm = _world_bm(o)
            try:
                out[o.name] = _obj_boxes(bm, o.name)
            finally:
                bm.free()
    return out


def _ft_boxes_all(name):
    bm = _world_bm(bpy.data.objects[name])
    try:
        return _obj_boxes(bm, name)
    finally:
        bm.free()


def _box_area_plan(bs):
    return sum((b[3] - b[0]) * (b[4] - b[1]) for b in bs)


def _wp_area(bs):
    return sum((b[3] - b[0]) * (b[4] - b[1]) if b[5] - b[2] < 0.01 else max(b[3] - b[0], b[4] - b[1]) * (b[5] - b[2]) for b in bs)


def tiles_report():
    q = bpy.data.objects["FT_Qty"]
    out = []
    for k, f in FT.items():
        a, b, t = f["size"]
        need = q[f"{k}_need"]
        area = q[f"{k}_area"]
        bags = area / (ADH["big"] if max(a, b) >= 0.40 else ADH["small"])
        g = _grout_kg(area, a, b, f["joint"], t) * (1 + GROUT["waste"])
        out.append(f"{f['th']}: {area:.2f} ตร.ม. (เต็มแผ่น {q[f'{k}_whole']} + ตัด {q[f'{k}_cut']} + ลูกตั้ง {q[f'{k}_strips']}) "
                   f"+ {SPARE * 100:.0f} % = {need} แผ่น → {math.ceil(need / f['box'] - 1e-9)} กล่อง ({f['box']} แผ่น/กล่อง) "
                   f"[สูตร ×1.10 = {math.ceil(area * 1.10 / (a * b) - 1e-9)} แผ่น] · ปูนกาว {math.ceil(bags - 1e-9)} ถุง · ยาแนว {g:.1f} กก.")
    bx = _ft_boxes()
    sc = [b for n, v in bx.items() if n.endswith("_Screed") for b in v]
    out.append(f"{SCREED['th']}: {_box_area_plan(sc):.2f} ตร.ม. หนาเฉลี่ย {sum(_vol(b) for b in sc) / max(_box_area_plan(sc), 1e-9) * 1000:.0f} มม. "
               f"= {sum(_vol(b) for b in sc):.3f} ลบ.ม.")
    r = qto(C_TILE, [b for (el, _), x in qto(C_GB).items() if el == "concrete" for b in x["boxes"]])
    sc_, sd = r[("concrete", "STEP")], r[("sand", "STEP")]
    exv = sum(_vol(b) for b in _ft_boxes_all("FT_Step_Exc"))
    ml = sum(r[("mesh", "STEP")]["bars"])
    out.append(f"บันได ค.ส.ล. {len(STEPS['flights'])} จุด ({STEPS['rise']} ลูกตั้ง × {(FL_WET - GL) / STEPS['rise']:.3f}): คอนกรีต {sc_['vol']:.3f} ลบ.ม. · "
               f"ไม้แบบ {max(sc_['side'], 0):.2f} ตร.ม. · ทราย {sd['vol']:.3f} ลบ.ม. · ขุดดิน {exv:.3f} ลบ.ม. · ไวร์เมช {ml * STEPS['mesh_s'] / 2:.2f} ตร.ม."
               f" (กระเบื้อง FL3 ลูกนอน/ลูกตั้งรวมในแถว FL3 ด้านบน)")
    wp = bx.get("FT_Waterproof", [])
    a = _wp_area(wp)
    out.append(f"{WP['th']}: {a:.2f} ตร.ม. (พื้น + ผนัง {WP['up']:.2f} / ที่อาบน้ำ {WP['shower']:.2f}) × {WP['kg']} กก./ตร.ม. "
               f"= {a * WP['kg']:.1f} กก. → {math.ceil(a * WP['kg'] / WP['bag'] - 1e-9)} ถัง · {WP['mesh']} {q['mesh']:.1f} ม. "
               f"→ {math.ceil(q['mesh'] / WP['roll'] - 1e-9)} ม้วน")
    return "\n".join(out)


# ---------------------------------------------------------------- ST11 selfcheck

def _check_tiles(rows_before):
    """Read back: floor levels per structure, every floored point covered (5 cm), no finish inside the structure or
    the walls, joints = spec, pieces ≤ a tile, bath walls covered to the ceiling, waterproofing heights, risers at
    every level change, counts = layout + 3 %."""
    bx = _ft_boxes()
    assert bx, "[count] no tiles"
    fails = []
    # pieces: level and size per zone, joints between neighbours
    for z, tp in FLOOR_ZONES.items():
        tiles = bx.get(f"FT_{z}_Tiles", [])
        if not tiles:
            fails.append(f"[count] zone {z}: no tiles")
            continue
        f = FT[tp]
        a, b, t = f["size"]
        jw, lvl = f["joint"], f["level"]
        lv = bpy.data.objects[f"FT_{z}_Tiles"].data
        if lv.get("type") != tp:
            fails.append(f"[zone] {z}: tiles {lv.get('type')} != A-02/A-04 {tp}")
        for x in tiles:
            if abs(x[5] - lvl) > 1e-5 or abs(x[5] - x[2] - t) > 1e-5:
                fails.append(f"[level] {z}: tile at {x[0]:.2f}, {x[1]:.2f} z {x[2]:.4f}..{x[5]:.4f} (+{lvl:.2f}, t {t})")
                break
        big = [x for x in tiles if x[3] - x[0] > a + 1e-5 or x[4] - x[1] > b + 1e-5]
        if big:
            fails.append(f"[size] {z}: {len(big)} pieces bigger than {a}×{b}")
        xs = sorted(tiles)
        for p in xs:
            nb = [q for q in xs if 1e-6 < q[0] - p[3] < 0.01 and min(p[4], q[4]) - max(p[1], q[1]) > 0.01]
            bad = [q for q in nb if abs(q[0] - p[3] - jw) > 1e-5 and not any(   # a piece between them: not neighbours
                r is not q and p[3] - 1e-7 <= r[0] < q[0] - 1e-7 and
                r[1] <= (max(p[1], q[1]) + min(p[4], q[4])) / 2 <= r[4] for r in xs if r[0] < p[3] + 0.01)]
            if bad:
                fails.append(f"[joints] {z}: {(bad[0][0] - p[3]) * 1000:.1f} mm joint at x {p[3]:.3f}, spec {jw * 1000:.0f} mm")
                break
    # coverage: sample the plan every 5 cm; a point over the structure and clear of walls / columns is floored
    conc = [b for cn in (C_GB, C_FLOOR) for (el, _), x in qto(cn).items() if el == "concrete" for b in x["boxes"]]
    obst = _obstacles()
    tops = [b for n, v in bx.items() if n.endswith("_Tiles") or n.endswith("_Grout") for b in v]
    rz = bx.get("FT_Risers", [])
    gc, go, gt, gr = _Grid(conc), _Grid(obst), _Grid(tops), _Grid(rz + bx.get("FT_RiserBed", []))
    bare, wrong = [], []
    xs0, ys0 = min(b[0] for b in conc), min(b[1] for b in conc)
    xs1, ys1 = max(b[3] for b in conc), max(b[4] for b in conc)
    x = xs0 + 0.0123
    while x < xs1:
        y = ys0 + 0.0177
        while y < ys1:
            st = max((b[5] for b in gc.near((x, y, 0.5, x, y, 0.8)) if b[0] <= x <= b[3] and b[1] <= y <= b[4] and b[5] < 0.79), default=None)
            if st is not None:
                fl = st + FINISH
                pt = lambda zz: (x, y, zz, x, y, zz)
                if not any(b[0] < x < b[3] and b[1] < y < b[4] and b[2] < fl - 0.002 and b[5] > st + 0.002 for b in go.near(pt(fl - 0.01), 0.02)):
                    over_riser = any(b[0] <= x <= b[3] and b[1] <= y <= b[4] for b in gr.near(pt(0.75), 0.02))
                    want = FL2 if over_riser else fl
                    hit = [b for b in gt.near(pt(want - 0.001), 0.01) if b[0] - 1e-6 <= x <= b[3] + 1e-6 and b[1] - 1e-6 <= y <= b[4] + 1e-6]
                    if not hit:
                        bare.append((round(x, 3), round(y, 3)))
                    elif any(abs(b[5] - want) > 1e-5 for b in hit):
                        wrong.append((round(x, 3), round(y, 3)))
            y += 0.05
        x += 0.05
    wall_t = bx.get("FT_Wall_Tiles", [])
    gw = _Grid(wall_t + bx.get("FT_Wall_Bed", []) + [b for b in bx.get("FT_Waterproof", []) if b[5] - b[2] > 0.01])
    bare = [p for p in bare if not any(b[0] - 1e-6 <= p[0] <= b[3] + 1e-6 and b[1] - 1e-6 <= p[1] <= b[4] + 1e-6 and b[2] < FL_WET
                                       for b in gw.near((p[0], p[1], FL_WET - 0.003, p[0], p[1], FL_WET - 0.003), 0.01))]
    if bare:
        fails.append(f"[coverage] {len(bare)} floor sample points bare, first {bare[:3]}")
    if wrong:
        fails.append(f"[level] {len(wrong)} floor points tiled at the wrong level for their structure, first {wrong[:3]}")
    # no finish inside the structure, walls, columns or ceilings; no two finish boxes share volume
    finish = [b for v in bx.values() for b in v]
    solid = conc + obst + [b for (el, _), x in qto(C_COL).items() if el == "concrete" for b in x["boxes"]] + \
        [b for (el, _), x in qto(C_CEIL).items() if el in ("ceiling", "soffit") for b in x["boxes"]]
    gs = _Grid(solid)
    inside = [f for f in finish if any((i := _inter(f, s)) and min(i[k + 3] - i[k] for k in range(3)) > 1e-5 for s in gs.near(f))]
    if inside:
        fails.append(f"[clash] {len(inside)} finish boxes inside the structure / walls, first {tuple(round(v, 3) for v in inside[0])}")
    cl = _clashes(finish, 1e-9)
    if cl:
        fails.append(f"[overlap] {len(cl)} finish box pairs share volume, first {tuple(round(v, 3) for v in cl[0][0])}")
    # risers: one at every FL2 → +0.70 edge, from the lower screed to under the FL2 bed
    zones = _floor_zones()
    for z, ax, pl, lo, hi, sg in _risers(zones):
        f = FT[zones[z][0]]
        mid = (lo + hi) / 2
        p = [0.0, 0.0]
        p[ax], p[1 - ax] = pl + sg * (f["bed"] + f["size"][2] / 2), mid
        if not any(b[0] <= p[0] <= b[3] and b[1] <= p[1] <= b[4] and b[2] <= FL_WET and b[5] >= FL2 - 0.02 for b in rz):
            fails.append(f"[riser] no riser tile at the level change {'xy'[ax]} {pl:.3f} ({lo:.2f}..{hi:.2f})")
    # bath walls: every seen face point inside the tiled height under a tile or in a joint (5 cm), up to the ceiling
    w3 = FT["W3"]
    wb = w3["bed"] + w3["size"][2]
    jw = w3["joint"]
    boards = [b for (el, _), x in qto(C_CEIL).items() if el == "ceiling" for b in x["boxes"]]
    rooms = _ceiling_rooms()
    for bath, fl in _bath_faces().items():
        rr = rooms[bath][3]
        zc = min(b[2] for b in boards if rr[0] - 0.05 <= (b[0] + b[3]) / 2 <= rr[2] + 0.05 and rr[1] - 0.05 <= (b[1] + b[4]) / 2 <= rr[3] + 0.05)
        mine = [b for b in wall_t if rr[0] - 0.05 <= (b[0] + b[3]) / 2 <= rr[2] + 0.05 and rr[1] - 0.05 <= (b[1] + b[4]) / 2 <= rr[3] + 0.05]
        if not mine or abs(max(b[5] for b in mine) - zc) > 1e-4:
            fails.append(f"[wall] {bath}: wall tiles up to {max((b[5] for b in mine), default=0):.3f}, ceiling {zc:.3f} (A-13: to the ceiling)")
        z_lo = FL_WET - FT["FL4"]["size"][2] - FT["FL4"]["bed"]
        gm = _Grid(mine)
        nb = 0
        for ax, sg, pl, pcs in fl:
            for r in pcs:
                u = r[0] + 0.0213
                while u < r[2] - 0.001:
                    zz = max(r[1], z_lo) + 0.0117
                    while zz < r[3] - 0.001:
                        P = [0.0, 0.0, zz]
                        P[ax], P[1 - ax] = pl + sg * (wb - 0.001), u
                        q = (P[0] - jw - 1e-4, P[1] - jw - 1e-4, zz - jw - 1e-4, P[0] + jw + 1e-4, P[1] + jw + 1e-4, zz + jw + 1e-4)
                        if not gm.near(q):
                            nb += 1
                        zz += 0.05
                    u += 0.05
        if nb:
            fails.append(f"[wall] {bath}: {nb} wall sample points bare")
    # waterproofing: the bath floors whole; walls exactly to 0.30 / 1.80 (shower bay), every 5 cm along each face
    wp = bx.get("FT_Waterproof", [])
    wenv = bx.get("FT_Wall_Tiles", []) + bx.get("FT_Wall_Bed", [])
    for bath, fl in _bath_faces().items():
        rs = zones[bath][3]
        got = sum((b[3] - b[0]) * (b[4] - b[1]) for b in wp if b[5] - b[2] < 0.01 and any(
            r[0] - 1e-6 <= b[0] and b[3] <= r[2] + 1e-6 and r[1] - 1e-6 <= b[1] and b[4] <= r[3] + 1e-6 for r in rs))
        want = sum((r[2] - r[0]) * (r[3] - r[1]) for r in rs)
        if abs(got - want) > 1e-5 * max(want, 1):
            fails.append(f"[waterproof] {bath}: floor coat {got:.3f} m², floor {want:.3f}")
        sx = SHOWER[bath]
        for ax, sg, pl, pcs in fl:
            for r in pcs:
                if r[1] > FL_WET:
                    continue
                u = r[0] + 0.0213
                while u < r[2] - 0.001:
                    xm = u if ax == 1 else pl
                    h = FL_WET + (WP["shower"] if sx[0] <= xm <= sx[1] else WP["up"])
                    h = min(h, r[3])
                    for zz, want in ((h - 0.01, True), (h + 0.01, False)):
                        P = [0.0, 0.0, zz]
                        P[ax], P[1 - ax] = pl + sg * WP["t"] / 2, u
                        has = any(b[0] - 1e-6 <= P[0] <= b[3] + 1e-6 and b[1] - 1e-6 <= P[1] <= b[4] + 1e-6 and b[2] <= zz <= b[5] for b in wp)
                        if want and not has:   # behind the next face's tiles at an inside corner: that face's coat is there
                            has = any(b[0] < P[0] < b[3] and b[1] < P[1] < b[4] and b[2] < zz < b[5] and
                                      b[4 - ax] - b[1 - ax] < b[ax + 3] - b[ax] for b in wenv)   # a face across this one
                        if has != want and not (zz > r[3]):
                            fails.append(f"[waterproof] {bath}: coat {'short of' if want else 'over'} {h - FL_WET:.2f} at {'xy'[1 - ax]} {u:.2f}")
                            break
                    u += 0.05
    # steps: equal risers <= 0.18, treads >= 0.25; every tread tiled at its level edge to edge, every riser face tiled,
    # the concrete one tile + bed under each tread, the floor it leaves reaching over riser 1
    tr, rs_, sc = bx.get("FT_Step_Treads", []), bx.get("FT_Step_Risers", []), bx.get("FT_Step_Conc", [])
    gtr, grs, gsc = _Grid(tr), _Grid(rs_), _Grid(sc)
    for nm in STEPS["flights"]:
        f, ax, E, sg, eps, r, h, c = _step_geom(nm)
        lo, hi = f["span"]
        rises = [h[i] - h[i + 1] for i in range(len(h) - 1)]
        if max(rises) - min(rises) > 1e-6 or max(rises) > 0.18 + 1e-6 or min(f["treads"]) < 0.25 - 1e-6:
            fails.append(f"[steps] {nm}: risers {[round(x, 3) for x in rises]}, treads {f['treads']}")
        at = (lambda d, u: (E + sg * d, u)) if ax == 0 else (lambda d, u: (u, E + sg * d))
        gap = 0
        for i in range(1, len(c)):
            dd = c[i - 1] + 0.013
            while dd < c[i] + eps - 0.002:
                u = lo + 0.0213
                while u < hi - 0.001:
                    x, y = at(dd, u)
                    top = [b for b in gtr.near((x, y, h[i] - 0.004, x, y, h[i] - 0.004), 1e-4) if b[0] <= x <= b[3] and b[1] <= y <= b[4]]
                    if not top or any(abs(b[5] - h[i]) > 1e-5 for b in top):
                        gap += 1
                    u += 0.05
                dd += 0.05
            x, y = at((c[i - 1] + c[i]) / 2, (lo + hi) / 2)
            if not any(b[0] <= x <= b[3] and b[1] <= y <= b[4] and abs(b[5] - (h[i] - eps)) < 1e-5 for b in sc):
                fails.append(f"[steps] {nm}: tread {i} concrete not {eps * 1000:.0f} mm under its finish")
        for i in range(1, len(c) + 1):
            z0, z1 = (h[i] if i < len(c) else GL), h[i - 1] - eps
            u = lo + 0.0213
            while u < hi - 0.001:
                zz = z0 + 0.01
                while zz < z1 - 0.005:
                    x, y = at(c[i - 1] + eps - 0.002, u)
                    if not any(b[0] <= x <= b[3] and b[1] <= y <= b[4] and b[2] <= zz <= b[5] for b in grs.near((x, y, zz, x, y, zz), 1e-4)):
                        gap += 1
                    zz += 0.05
                u += 0.05
        x, y = at(eps / 2, (lo + hi) / 2)
        zt = bx.get(f"FT_{f['zone']}_Tiles", [])
        if not any(b[0] <= x <= b[3] and b[1] <= y <= b[4] and abs(b[5] - h[0]) < 1e-5 for b in zt):
            fails.append(f"[steps] {nm}: the {f['zone']} tile does not reach over riser 1")
        if gap:
            fails.append(f"[steps] {nm}: {gap} tread / riser sample points bare")
    # counts = layout + 3 %
    q = bpy.data.objects["FT_Qty"]
    for k in FT:
        if q[f"{k}_need"] != math.ceil((q[f"{k}_whole"] + q[f"{k}_cut"] + q[f"{k}_strips"]) * (1 + SPARE) - 1e-9):
            fails.append(f"[count] {k}: tiles to order {q[f'{k}_need']} != layout + {SPARE * 100:.0f} %")
    if fails:
        raise AssertionError(f"{len(fails)} failing in tiles:\n" + "\n".join(fails[:12]))
    ar = {z: _box_area_plan(bx.get(f"FT_{z}_Tiles", []) + bx.get(f"FT_{z}_Grout", [])) for z in FLOOR_ZONES}
    return "ST11 ok: " + " · ".join(f"{z} {a:.2f} m²" for z, a in ar.items()) + f" · bath walls {q['W3_area']:.2f} m², {len(rz)} risers"
