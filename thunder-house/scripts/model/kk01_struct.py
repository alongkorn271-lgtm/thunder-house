"""KK01 บ้านเกาะคา – construction model, structure stages (stage-by-stage build, adapted from common practice's E42 e42_struct.py).

  ST00 grid · ST01 ฐานแผ่ F1 (pit, compacted sand, lean concrete, rebar mat, footing concrete)
  ST02 ตอม่อ P1 (stub concrete, 6-DB12 starters with L-foot on the mat + lap, RB6 ties)

Each stub = an empty P1_<grid> at the footing top (z −1.25), children _Conc, _Bars, _Ties; equal stubs share data.
Each footing = an empty F1_<grid> at the footing's bottom centre, parenting one object per work item:
_Exc (pit: wire, take-off only, never rendered), _Sand, _Lean, _Conc, _Rebar (curve, one spline per bar).
Identical footings share their mesh/curve data. Specs live on the data as custom props; qto() reads only those + geometry.
Numbers: Construction/FACTS.md, ST01_footings_spec.md, ST02_stubs_spec.md.

    exec(open(<scripts>/kk01_load.py).read()); build_grid(); build_footings(); print(report()); print(selfcheck())
"""
import bpy, bmesh, itertools, math, re

GL = 0.00                                                       # ระดับดินเดิม
GX = {"1": 0.0, "2": 3.5, "3": 5.0, "4": 6.5, "5": 9.5, "6": 13.0}
GY = {"G": 0.0, "F": 3.0, "E": 4.0, "D": 4.5, "C": 7.5, "B": 9.2, "A": 12.2}
FOOTINGS = {"F1": ["A2", "A4", "A5", "B2", "B4", "B5", "C1", "C2", "C3", "C5", "C6", "D5", "D6",
                   "E1", "E2", "E3", "F5", "F6", "G1", "G2", "G3", "G5", "G6"]}   # S-01, 23 ฐาน
# S-03 SECTION F1C: footing underside −1.50, lean 0.05, sand 0.10 → pit bottom exc −1.65.
# pad / work / covers / hook: assumed (ST01 spec).
TYPES = {"F1": dict(B=1.20, T=0.25, exc=-1.65, sand=0.10, lean=0.05, pad=0.05, work=0.20,
                    d=0.012, s=0.125, side=0.05, bottom=0.075, top=0.03, hook=0.12,
                    grade="St.240 ksc", bar="DB12 SD40")}
TYPES = {k: {**t, "bot": t["exc"] + t["sand"] + t["lean"]} for k, t in TYPES.items()}   # footing bottom
FOOT_BOT = -1.50                                                # S-03: checked against TYPES, not derived from it
# Ground beams (A-10/A-11 sections, scaled; user confirmed 5 พ.ย. 69): A-04 levels are FINISHED floors (user, ST11:
# +0.80 = tile face) → FL2 +0.80 = beam top + PS 0.05 + topping 0.05 + finish 0.03, every beam B1/B2/B3 0.20 × 0.40
# with top +0.67, bottom +0.27; verandah/bath FL3/FL4 +0.70 = slab top +0.67 + finish 0.03 (only the slab drops).
# Beam points: grid names plus off-grid beam lines of S-02 (x 1a = 2.5, 5a = 10.5; y Ga = 1.0, Gb = 2.5); a point is
# <y label><x label>, e.g. "Gb1a" = (2.5, 2.5). Stubs keep their grid names.
PX = {**GX, "1a": 2.5, "5a": 10.5}
PY = {**GY, "Ga": 1.0, "Gb": 2.5}
GB_D, GB_TOP = 0.40, 0.67
# S-02 read span by span (ST03, 5 พ.ย. 69): (from, to, top, type B1/B2/B3 by the label next to the span). Unlabelled:
# E3–E5 → B1 like E2–E3 (assumed). Corners A5a and B6 have no column (beam on beam / cantilever as drawn: engineer).
GB_LINES = [(a, b, GB_TOP, tp) for a, b, tp in (
    ("A2", "A4", "B2"), ("A4", "A5", "B2"), ("A5", "A5a", "B2"),
    ("B2", "B4", "B2"), ("B4", "B5", "B2"), ("B5", "B5a", "B3"), ("B5a", "B6", "B1"),
    ("C1", "C2", "B2"), ("C2", "C3", "B1"), ("C3", "C4", "B3"), ("C4", "C5", "B3"), ("C5", "C6", "B2"),
    ("D5", "D5a", "B3"), ("D5a", "D6", "B3"),
    ("E1", "E1a", "B3"), ("E1a", "E2", "B3"), ("E2", "E3", "B1"), ("E3", "E5", "B1"),
    ("F5", "F5a", "B3"), ("F5a", "F6", "B3"),
    ("Gb1", "Gb1a", "B3"), ("Gb1a", "Gb2", "B3"),
    ("Ga3", "Ga5", "B1"),
    ("G1", "G2", "B2"), ("G2", "G3", "B1"), ("G3", "G5", "B2"), ("G5", "G6", "B2"),
    ("C1", "E1", "B2"), ("E1", "Gb1", "B3"), ("Gb1", "G1", "B3"),
    ("E1a", "Gb1a", "B1"),
    ("A2", "B2", "B2"), ("B2", "C2", "B1"),
    ("E2", "Gb2", "B3"), ("Gb2", "G2", "B3"),
    ("C3", "E3", "B2"), ("E3", "Ga3", "B3"), ("Ga3", "G3", "B3"),
    ("A4", "B4", "B2"), ("B4", "C4", "B1"),
    ("A5", "B5", "B2"), ("B5", "C5", "B1"), ("C5", "D5", "B2"), ("D5", "E5", "B3"), ("E5", "F5", "B3"),
    ("F5", "Ga5", "B3"), ("Ga5", "G5", "B3"),
    ("A5a", "B5a", "B1"), ("D5a", "F5a", "B1"),
    ("B6", "C6", "B2"), ("C6", "D6", "B2"), ("D6", "F6", "B1"), ("F6", "G6", "B2"))]
STUB_TOP = 0.27                                                 # beam bottom (ST11 levels): checked against GB_LINES, not derived
STUB_GRIDS = {"P1": FOOTINGS["F1"]}
# S-03 C1 ฐานราก–พื้น: 0.20 × 0.20, 6-DB12 (3 on each of two faces), STR RB6 @0.15 uniform (user, not S-04),
# cover 0.03 to the tie (S-03, user). The 6 starters: L-foot 0.20 on the mat's top layer → beam top + lap 0.60 (50d,
# user: the 4 column bars lap there in ST05). Ties: stub only, first/last 5 cm from its ends, 135° hooks 75 mm (assumed).
STUBS = {"P1": dict(b=0.20, cover=0.03, d=0.012, nbar=6, foot=0.20, lap=0.60, dt=0.006, s=0.15, first=0.05,
                    hook=0.075, grade="St.240 ksc", bar="DB12 SD40", tie="RB6 SR24")}
# S-03 beam sections, all 0.20 × 0.40 DB12, ป-RB6 @0.15. Continuous: 2 top + 2 bottom (laps where a line passes
# one 10 m stock bar). B1: + 1 bottom bar through each B1 span (3-DB12 at mid and support). B2 / B3: + 2 / 3 specials
# on the tension side (user rule from common practice: bottom 0.8 L centred, top L/4 into every span beside a support,
# hooked into the joint at a line end). Cover 0.03, 90° hooks 0.15 into the end joints, lap 0.60 (50d): top bars lap
# mid-span, bottom bars over a support. Under every beam (bottom +0.27 is 0.27 above GL): compacted sand GL → +0.22 and
# lean 0.05, `pad` wider each side, no bottom form (assumed, like the contractor's BOQ sand + lean for the beams).
GBEAM = dict(b=0.20, h=GB_D, cover=0.03, d=0.012, hook=0.15, dt=0.006, s=0.15, first=0.05, shook=0.075,
             mid=0.8, sup=0.25, lap=0.60, lean=0.05, pad=0.05, grade="St.240 ksc", bar="DB12 SD40", tie="RB6 SR24")
BEAM_TYPES = {"B1": dict(extra=1, nsp=0), "B2": dict(extra=0, nsp=2), "B3": dict(extra=0, nsp=3)}
KG_M = {4: 0.099, 6: 0.222, 9: 0.499, 12: 0.888, 16: 1.578}
STOCK = 10.0
C_GRID, C_FOOT, C_STUB, C_GB = "KK01 ST00 Grid", "KK01 ST01 Footings", "KK01 ST02 Stubs", "KK01 ST03 Ground beams"
STAGES = [C_FOOT, C_STUB, C_GB]


def _coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def _clear(name):
    c = _coll(name)
    for o in list(c.objects):
        bpy.data.objects.remove(o)
    return c


def _drop(store, name):
    d = store.get(name)
    if d:
        store.remove(d)


def _boxes_data(name, boxes, m=None, **props):
    """One mesh of disjoint boxes, 8 vertices each in creation order (_obj_boxes reads them back that way)."""
    _drop(bpy.data.meshes, name)
    bm = bmesh.new()
    for x0, y0, z0, x1, y1, z1 in boxes:
        assert min(x1 - x0, y1 - y0, z1 - z0) > 1e-6, f"{name}: a box under 1 µm thick"
        for v in bmesh.ops.create_cube(bm, size=1.0)["verts"]:   # outward normals
            v.co = (x0 if v.co.x < 0 else x1, y0 if v.co.y < 0 else y1, z0 if v.co.z < 0 else z1)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if m:
        me.materials.append(m)
    me.update(calc_edges=True)
    for k, v in props.items():
        me[k] = v
    return me


def _box_data(name, x0, y0, z0, x1, y1, z1, m=None, **props):
    return _boxes_data(name, [(x0, y0, z0, x1, y1, z1)], m, **props)


def _mat_bars(t):
    """Two layers of hooked bars [(points...)] relative to the footing bottom centre; layer 2 runs along y on top."""
    d, e = t["d"], t["B"] / 2 - t["side"] - t["d"] / 2
    n = math.ceil(2 * e / t["s"] - 1e-9) + 1                    # spacing never above s
    assert t["bottom"] + 2 * d + t["hook"] <= t["T"] - t["top"] + 1e-9, "hooks leave less than the top cover"
    bars = []
    for layer, (ee, z) in enumerate(((e, t["bottom"] + d / 2), (e - d, t["bottom"] + 1.5 * d))):
        for i in range(n):
            p = -ee + i * 2 * ee / (n - 1)
            pts = [(-ee, p, z + t["hook"]), (-ee, p, z), (ee, p, z), (ee, p, z + t["hook"])]
            bars.append([(y, x, z) for x, y, z in pts] if layer else pts)
    return bars


def _rebar_data(name, bars, d, m, **props):
    _drop(bpy.data.curves, name)
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions, cu.bevel_mode, cu.bevel_depth, cu.bevel_resolution, cu.use_fill_caps = "3D", "ROUND", d / 2, 1, True
    for pts in bars:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for P, c in zip(sp.points, pts):
            P.co = (*c, 1.0)
    cu.materials.append(m)
    for k, v in props.items():
        cu[k] = v
    return cu


def build_grid(ext=1.5, size=0.5):
    """ST00: grid lines at ground level + labels (never rendered)."""
    c = _clear(C_GRID)
    ink = mat("M_GridLabel", (0.95, 0.80, 0.15), 0.5)
    xs, ys = sorted(GX.values()), sorted(GY.values())
    V, E = [], []
    for x in xs:
        V += [(x, ys[0] - ext, GL), (x, ys[-1] + ext, GL)]
        E.append((len(V) - 2, len(V) - 1))
    for y in ys:
        V += [(xs[0] - ext, y, GL), (xs[-1] + ext, y, GL)]
        E.append((len(V) - 2, len(V) - 1))
    _drop(bpy.data.meshes, "Grid_Lines")
    me = bpy.data.meshes.new("Grid_Lines")
    me.from_pydata(V, E, [])
    objs = [bpy.data.objects.new("Grid_Lines", me)]
    labels = [(k, (x, ys[0] - ext - size, GL)) for k, x in GX.items()] + \
             [(k, (xs[0] - ext - size, y, GL)) for k, y in GY.items()]
    for k, loc in labels:
        _drop(bpy.data.curves, f"Grid_{k}")
        tx = bpy.data.curves.new(f"Grid_{k}", "FONT")
        tx.body, tx.size, tx.align_x, tx.align_y = k, size, "CENTER", "CENTER"
        tx.materials.append(ink)
        o = bpy.data.objects.new(f"Grid_{k}", tx)
        o.location = loc
        objs.append(o)
    for o in objs:
        o.hide_render = True
        c.objects.link(o)
    return len(objs)


def build_footings():
    """ST01: every footing type in TYPES at its grid points in FOOTINGS."""
    pts = [g for v in FOOTINGS.values() for g in v]
    assert len(pts) == len(set(pts)) and set(FOOTINGS) == set(TYPES), "grid point used twice or type without size"
    c = _clear(C_FOOT)
    conc = mat("M_Concrete", (0.50, 0.50, 0.48), 0.85)
    lean = mat("M_LeanConcrete", (0.30, 0.30, 0.28), 0.95)
    sand = mat("M_Sand", (0.76, 0.68, 0.52), 0.95)
    steel = mat("M_Rebar", (0.28, 0.17, 0.11), 0.55, 0.6)
    n = 0
    for tn, t in TYPES.items():
        h, q, w = t["B"] / 2, t["B"] / 2 + t["pad"], t["B"] / 2 + t["work"]
        zs, zl = -(t["sand"] + t["lean"]), -t["lean"]
        D = {
            "Exc": _box_data(f"{tn}_Exc", -w, -w, zs, w, w, GL - t["bot"], None,
                             element="excavation", th="ขุดดินฐานราก", type=tn),
            "Sand": _box_data(f"{tn}_Sand", -q, -q, zs, q, q, zl, sand,
                              element="sand", th=f"ทรายหยาบบดอัดแน่น {t['sand'] * 100:.0f} ซม.", type=tn),
            "Lean": _box_data(f"{tn}_Lean", -q, -q, zl, q, q, 0, lean,
                              element="lean_concrete", th=f"คอนกรีตหยาบ {t['lean'] * 100:.0f} ซม.", type=tn),
            "Conc": _box_data(f"{tn}_Conc", -h, -h, 0, h, h, t["T"], conc,
                              element="concrete", th="คอนกรีตฐานราก", type=tn, grade=t["grade"]),
            "Rebar": _rebar_data(f"{tn}_Rebar", _mat_bars(t), t["d"], steel, element="rebar", th="เหล็กเสริมฐานราก",
                                 type=tn, bar=t["bar"], dia_mm=round(t["d"] * 1000), spacing=t["s"]),
        }
        for g in FOOTINGS[tn]:
            root = bpy.data.objects.new(f"{tn}_{g}", None)
            root.empty_display_type, root.empty_display_size = "PLAIN_AXES", 0.3
            root.location = (GX[g[1:]], GY[g[0]], t["bot"])
            root["grid"], root["type"] = g, tn
            c.objects.link(root)
            for k, data in D.items():
                o = bpy.data.objects.new(f"{tn}_{g}_{k}", data)
                o.parent = root
                c.objects.link(o)
                if k == "Exc":
                    o.display_type, o.hide_render = "WIRE", True
            n += 1
    bpy.context.view_layer.update()
    return n


# ---------------------------------------------------------------- ST02 stubs

def _pxy(p):
    """(x, y) of a beam point name: <y label (A-G + optional a-z)><x label (digit + optional a-z)>."""
    m = re.fullmatch(r"([A-G][a-z]?)(\d[a-z]?)", p)
    assert m and m[1] in PY and m[2] in PX, f"unknown point {p}"
    return PX[m[2]], PY[m[1]]


def _on_span(p, a, b):
    """Point p lies on segment a-b (ends included)."""
    (x, y), (xa, ya), (xb, yb) = _pxy(p), _pxy(a), _pxy(b)
    return (xa == xb == x and min(ya, yb) <= y <= max(ya, yb)) or (ya == yb == y and min(xa, xb) <= x <= max(xa, xb))


def _tops_at(g):
    """(top, bottom) of every ground beam passing over point g (ends and mid-span)."""
    out = []
    for a, b, top, _ in GB_LINES:
        (xa, ya), (xb, yb) = _pxy(a), _pxy(b)
        assert (xa == xb) != (ya == yb), f"beam {a}-{b} not along a grid line"
        if _on_span(g, a, b):
            out.append((top, top - GB_D))
    return out


def _stub_levels():
    """grid -> (stub bottom = footing top, stub top = lowest beam bottom, highest beam top, mat top-layer top z)."""
    lv = {}
    for sn, gs in STUB_GRIDS.items():
        for g in gs:
            tb = _tops_at(g)
            ft = [k for k, v in FOOTINGS.items() if g in v]
            assert tb and len(ft) == 1, f"stub {g}: no ground beam over it or no footing under it"
            f = TYPES[ft[0]]
            lv[g] = (f["bot"] + f["T"], min(b for _, b in tb), max(t for t, _ in tb), f["bot"] + f["bottom"] + 2 * f["d"])
    return lv


def _stub_geom(t):
    """(tie centreline half-size a, bar centre half-size m): tie at the cover, bars tight inside it."""
    a = t["b"] / 2 - t["cover"] - t["dt"] / 2
    return a, a - t["dt"] / 2 - t["d"] / 2


def _stub_bars(t, h, zf, top):
    """Starters and ties relative to the stub bottom centre; zf = top of the mat, top = starter top."""
    a, m = _stub_geom(t)
    assert t["nbar"] in (4, 6), "stub bars: 4 corners or 6 (3 on two faces)"
    assert h > 2 * t["first"], "stub too short for ties"
    zf += t["d"] / 2                                                # foot rests on the mat's top layer
    mains = [[(sx * (m + t["foot"]), sy * m, zf), (sx * m, sy * m, zf), (sx * m, sy * m, top)]
             for sx in (-1, 1) for sy in (-1, 1)]
    if t["nbar"] == 6:   # middle bars of the two y faces, foot turned outward along y
        mains += [[(0.0, sy * (m + t["foot"]), zf), (0.0, sy * m, zf), (0.0, sy * m, top)] for sy in (-1, 1)]
    nt = math.ceil((h - 2 * t["first"]) / t["s"] - 1e-9) + 1       # spacing never above s
    k = a - t["hook"] / math.sqrt(2)                                # 135° hooks into the core
    ties = [[(k, k, z), (a, a, z), (-a, a, z), (-a, -a, z), (a, -a, z), (a, a, z), (k, k, z)]
            for z in (t["first"] + i * (h - 2 * t["first"]) / (nt - 1) for i in range(nt))]
    return mains, ties, nt


def build_stubs():
    """ST02: stubs of STUBS at STUB_GRIDS, footing top → lowest beam bottom; equal stubs share one set of data."""
    pts = [g for v in STUB_GRIDS.values() for g in v]
    assert len(pts) == len(set(pts)) and set(STUB_GRIDS) == set(STUBS) and not set(STUBS) & set(TYPES), \
        "grid point used twice, stub type without size, or stub type named like a footing type"
    lv = _stub_levels()
    c = _clear(C_STUB)
    conc = mat("M_Concrete", (0.50, 0.50, 0.48), 0.85)
    steel = mat("M_Rebar", (0.28, 0.17, 0.11), 0.55, 0.6)
    n = 0
    for sn, t in STUBS.items():
        shared = {}
        for g in STUB_GRIDS[sn]:
            zb, zt, beam_top, zf = lv[g]
            h, top = zt - zb, beam_top + t["lap"] - zb
            key = f"{sn}_H{round(h * 100)}_T{round(top * 100)}"
            levels = (round(h, 6), round(top, 6), round(zf - zb, 6))
            if key not in shared:
                mains, ties, _ = _stub_bars(t, h, zf - zb, top)
                w = t["b"] / 2
                shared[key] = (levels, {
                    "Conc": _box_data(f"{key}_Conc", -w, -w, 0, w, w, h, conc,
                                      element="concrete", th="คอนกรีตตอม่อ", type=sn, grade=t["grade"]),
                    "Bars": _rebar_data(f"{key}_Bars", mains, t["d"], steel, element="rebar",
                                        th="เหล็กยืนตอม่อ (ขาตีนช้างบนตะแกรงฐาน ถึงหลังคาน + ระยะทาบ)",
                                        type=sn, bar=t["bar"], dia_mm=round(t["d"] * 1000)),
                    "Ties": _rebar_data(f"{key}_Ties", ties, t["dt"], steel, element="ties", th="เหล็กปลอกตอม่อ",
                                        type=sn, bar=t["tie"], dia_mm=round(t["dt"] * 1000), spacing=t["s"]),
                })
            assert shared[key][0] == levels, f"{key}: same name, other levels"
            root = bpy.data.objects.new(f"{sn}_{g}", None)
            root.empty_display_type, root.empty_display_size = "PLAIN_AXES", 0.2
            root.location = (GX[g[1:]], GY[g[0]], zb)
            root["grid"], root["type"] = g, sn
            c.objects.link(root)
            for k_, data in shared[key][1].items():
                o = bpy.data.objects.new(f"{sn}_{g}_{k_}", data)
                o.parent = root
                c.objects.link(o)
            n += 1
    bpy.context.view_layer.update()
    return n


# ---------------------------------------------------------------- measuring

def _world_bm(o):
    ev = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
    bm = bmesh.new()
    bm.from_mesh(ev.to_mesh())
    ev.to_mesh_clear()
    bm.transform(o.matrix_world)
    return bm


def _bar_lengths(o):
    return [sum((sp.points[i + 1].co.xyz - sp.points[i].co.xyz).length for i in range(len(sp.points) - 1))
            for sp in o.data.splines]


def _world_bars(o):
    M = o.matrix_world
    return [[M @ p.co.xyz for p in sp.points] for sp in o.data.splines]


def _vol(b):
    return (b[3] - b[0]) * (b[4] - b[1]) * (b[5] - b[2])


def _inter(a, b):
    lo, hi = [max(a[i], b[i]) for i in range(3)], [min(a[i + 3], b[i + 3]) for i in range(3)]
    return (*lo, *hi) if all(l < h for l, h in zip(lo, hi)) else None


def _union_volume(boxes):
    """Exact volume of a union of axis-aligned boxes: sum the grid cells that lie inside any box."""
    ax = [sorted({b[i] for b in boxes} | {b[i + 3] for b in boxes}) for i in range(3)]
    v = 0.0
    for x0, x1 in zip(ax[0], ax[0][1:]):
        for y0, y1 in zip(ax[1], ax[1][1:]):
            for z0, z1 in zip(ax[2], ax[2][1:]):
                c = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
                if any(all(b[i] < c[i] < b[i + 3] for i in range(3)) for b in boxes):
                    v += (x1 - x0) * (y1 - y0) * (z1 - z0)
    return v


def _obj_boxes(bm, name):
    """World boxes of a _boxes_data mesh (8 vertices per box, in creation order)."""
    vs = [v.co.copy() for v in bm.verts]
    assert vs and len(vs) % 8 == 0, f"not boxes: {name}"
    bs = [tuple(f(p[i] for p in vs[j:j + 8]) for f in (min, max) for i in range(3)) for j in range(0, len(vs), 8)]
    tot = sum(map(_vol, bs))
    assert abs(tot - bm.calc_volume()) <= 1e-5 * tot, f"not boxes: {name}"
    return bs


def _touch(a, b):
    """Area where two boxes meet on a vertical plane."""
    for k in (0, 1):
        if abs(a[k + 3] - b[k]) < 1e-5 or abs(b[k + 3] - a[k]) < 1e-5:
            o = [min(a[j + 3], b[j + 3]) - max(a[j], b[j]) for j in range(3) if j != k]
            if all(x > 1e-9 for x in o):
                return o[0] * o[1]
    return 0.0


def _stock_bars(lengths, stock=STOCK):
    """Stock bars needed to cut every length, offcuts reused (first-fit decreasing)."""
    free = []
    for L in sorted(lengths, reverse=True):
        assert L <= stock + 1e-9, f"piece {L:.3f} m longer than stock"
        i = next((i for i, f in enumerate(free) if f >= L - 1e-9), None)
        if i is None:
            free.append(stock - L)
        else:
            free[i] -= L
    return len(free)


def qto(coll=C_FOOT, against=()):
    """Measure every object whose data carries `element` + `type`: volume, formwork (vertical faces minus faces cast
    against other concrete of the stage, or against the world boxes in `against`: earlier stages / later columns),
    bar lengths. Rows per (element, type)."""
    rows, conc = {}, []
    for o in _coll(coll).objects:
        el = o.data.get("element") if o.data else None
        if not el or el in ("tile_bed", "steel"):   # sloped / profiled solids: measured by their own stages
            continue
        mw = o.matrix_world
        assert mw.determinant() > 0 and all(abs(s - 1) < 1e-9 for s in mw.to_scale()), f"scaled/mirrored: {o.name}"
        r = rows.setdefault((el, o.data["type"]), dict(th=o.data["th"], n=0, vol=0.0, side=0.0, bars=[], boxes=[],
                                                        dia=o.data.get("dia_mm"), bar=o.data.get("bar")))
        assert r["dia"] == o.data.get("dia_mm") and r["bar"] == o.data.get("bar"), f"two bar specs in one row: {o.name}"
        r["n"] += 1
        if o.type == "MESH":
            bm = _world_bm(o)
            assert all(len(e.link_faces) == 2 for e in bm.edges), f"open mesh: {o.name}"
            v = bm.calc_volume(signed=True)
            assert v > 0, f"inside-out: {o.name}"
            r["vol"] += v
            r["side"] += sum(f.calc_area() for f in bm.faces if abs(f.normal.z) < 1e-6)
            bs = [tuple(round(x, 5) for x in b) for b in _obj_boxes(bm, o.name)]
            r["boxes"] += bs
            if el == "concrete":
                conc += [(r, b) for b in bs]
            bm.free()
        else:
            r["bars"] += _bar_lengths(o)
    for (ra, a), (rb, b) in itertools.combinations(conc, 2):
        area = _touch(a, b)
        ra["side"] -= area
        rb["side"] -= area
    for ra, a in conc:
        for b in against:
            ra["side"] -= _touch(a, b)
    return rows


def report(coll=C_FOOT):
    r, out = qto(coll), []
    for (el, tn), x in r.items():
        if el == "excavation":
            out.append(f"{tn} {x['th']}: {x['n']} หลุม รวมรายหลุม {x['vol']:.3f} ลบ.ม.")
        elif x["bars"]:
            m = sum(x["bars"])
            groups = {}
            for L in x["bars"]:
                groups[round(L, 3)] = groups.get(round(L, 3), 0) + 1
            cut = " · ".join(f"{k} ท่อน × {L:.3f} ม." for L, k in sorted(groups.items())) if len(groups) <= 6 else                 f"{len(x['bars'])} ท่อน ({len(groups)} ขนาด {min(groups):.3f}–{max(groups):.3f} ม.)"
            out.append(f"{tn} {x['th']} {x['bar']}: {cut} = {m:.2f} ม. = {m * KG_M[x['dia']]:.1f} กก. "
                       f"→ ใช้เหล็กเส้น 10 ม. {_stock_bars(x['bars'])} เส้น (ใช้เศษตัดต่อ)")
        else:
            line = f"{tn} {x['th']}: {x['n']} ชิ้น = {x['vol']:.3f} ลบ.ม."
            if el == "concrete":
                line += f" · ไม้แบบ {x['side']:.2f} ตร.ม."
            out.append(line)
    poured = sum(x["vol"] for (el, _), x in r.items() if el == "concrete")
    if poured:
        out.append(f"คอนกรีตเทครั้งนี้ {poured:.3f} ลบ.ม. → สั่ง {math.ceil(poured * 2 - 1e-9) / 2:.1f} ลบ.ม.")
    pits = [b for (el, _), x in r.items() if el == "excavation" for b in x["boxes"]]
    if pits:
        merged = sum(1 for a, b in itertools.combinations(pits, 2) if _inter(a, b))
        out.append(f"ขุดดินสุทธิ {_union_volume(pits):.3f} ลบ.ม. (หลุมที่ซ้อนกัน {merged} คู่ นับครั้งเดียว)")
        solids = sum(x["vol"] for (el, _), x in r.items() if el in ("concrete", "lean_concrete", "sand"))
        out.append(f"ดินถมกลับหลุมถึงระดับดินเดิม (ก่อนงานตอม่อ) {_union_volume(pits) - solids:.3f} ลบ.ม.")
    if coll == C_STUB and r:
        rf = qto(C_FOOT)
        pits = [b for (el, _), x in rf.items() if el == "excavation" for b in x["boxes"]]
        solids = sum(x["vol"] for (el, _), x in rf.items() if el in ("concrete", "lean_concrete", "sand"))
        below = sum(_vol((b[0], b[1], b[2], b[3], b[4], min(b[5], GL))) for (el, _), x in r.items()
                    if el == "concrete" for b in x["boxes"] if b[2] < GL)
        above = sum(x["vol"] for (el, _), x in r.items() if el == "concrete") - below
        out.append(f"ตอม่อใต้ระดับดินเดิม {below:.3f} ลบ.ม. / เหนือดิน {above:.3f} ลบ.ม. → "
                   f"ดินถมกลับหลุมถึงระดับดินเดิม (หลังตอม่อ) {_union_volume(pits) - solids - below:.3f} ลบ.ม.")
    return "\n".join(out)


# ---------------------------------------------------------------- selfcheck (reads the model, tests the spec)

def _each(items, fn, what):
    fails = []
    for it in items:
        try:
            fn(it)
        except AssertionError as e:
            fails.append(str(e))
    if fails:
        raise AssertionError(f"{len(fails)} failing in {what}:\n" + "\n".join(fails[:12]))


def selfcheck():
    r, pits = qto(), []

    def eq(a, b, what):
        assert abs(a - b) <= 1e-5 * max(abs(b), 1e-9), f"[{what}] model {a:.6f} != expected {b:.6f}"
    tn, t = "F1", TYPES["F1"]
    assert abs(t["bot"] - FOOT_BOT) < 1e-9, f"[level] footing bottom {t['bot']} != S-03 {FOOT_BOT}"
    n, B, d = len(FOOTINGS[tn]), t["B"], t["d"]
    g = lambda el: r[(el, tn)]
    for el in ("concrete", "lean_concrete", "sand", "excavation", "rebar"):
        assert g(el)["n"] == n, f"[count] {el}: {g(el)['n']} objects, S-01 has {n} footings"
    eq(g("concrete")["vol"], n * B * B * t["T"], "concrete")
    eq(g("concrete")["side"], n * 4 * B * t["T"], "formwork")
    eq(g("lean_concrete")["vol"], n * (B + 2 * t["pad"]) ** 2 * t["lean"], "lean")
    eq(g("sand")["vol"], n * (B + 2 * t["pad"]) ** 2 * t["sand"], "sand")
    eq(g("excavation")["vol"], n * (B + 2 * t["work"]) ** 2 * (GL - t["exc"]), "pits")
    e = B / 2 - t["side"] - d / 2
    nb = math.ceil(2 * e / t["s"] - 1e-9) + 1
    eq(sum(g("rebar")["bars"]), n * nb * (2 * e + 2 * (e - d) + 4 * t["hook"]), "rebar length")

    # per footing: place, levels, layering, bars inside their covers, spacing — every fault in one run
    objs = {o.name: o for o in _coll(C_FOOT).objects}

    def one(gp):
        x, y = GX[gp[1:]], GY[gp[0]]
        root = objs.get(f"{tn}_{gp}")
        assert root, f"[count] {gp}: no footing"
        def box(k):
            bm = _world_bm(objs[f"{tn}_{gp}_{k}"])
            try:
                return _obj_boxes(bm, k)[0]
            finally:
                bm.free()
        c, l, s, p = box("Conc"), box("Lean"), box("Sand"), box("Exc")
        h = B / 2
        assert max(abs(c[0] - (x - h)), abs(c[3] - (x + h)), abs(c[1] - (y - h)), abs(c[4] - (y + h))) < 1e-5, \
            f"[position] {gp}: footing not centred on its grid point"
        assert abs(c[2] - FOOT_BOT) < 1e-5 and abs(c[5] - c[2] - t["T"]) < 1e-5, f"[level] {gp}: footing z {c[2]:.3f}..{c[5]:.3f}"
        assert abs(l[5] - c[2]) < 1e-5 and abs(l[5] - l[2] - t["lean"]) < 1e-5, f"[lean] {gp}: lean not 5 cm under the footing"
        assert abs(s[5] - l[2]) < 1e-5 and abs(s[5] - s[2] - t["sand"]) < 1e-5, f"[sand] {gp}: sand not under the lean"
        assert abs(p[2] - t["exc"]) < 1e-5 and abs(p[2] - s[2]) < 1e-5 and abs(p[5] - GL) < 1e-5, f"[pit] {gp}: pit {p[2]:.3f}..{p[5]:.3f}"
        assert all(p[i] <= l[i] + 1e-6 and p[i + 3] >= l[i + 3] - 1e-6 for i in (0, 1)), f"[pit] {gp}: pit narrower than the lean"
        bars = _world_bars(objs[f"{tn}_{gp}_Rebar"])
        r_ = d / 2
        for b in bars:
            xs, ys, zs = [q.x for q in b], [q.y for q in b], [q.z for q in b]
            assert min(xs) - r_ >= c[0] + t["side"] - 1e-5 and max(xs) + r_ <= c[3] - t["side"] + 1e-5 and \
                min(ys) - r_ >= c[1] + t["side"] - 1e-5 and max(ys) + r_ <= c[4] - t["side"] + 1e-5, f"[cover] {gp}: side cover"
            assert min(zs) - r_ >= c[2] + t["bottom"] - 1e-5, f"[cover] {gp}: bottom cover {min(zs) - r_ - c[2]:.3f}"
            assert max(zs) + r_ <= c[5] - t["top"] + 1e-5, f"[cover] {gp}: top cover"
        for axis in (0, 1):   # bars running along x sit at distinct y: spacing ≤ s, none doubled, both directions present
            run = [b for b in bars if abs(b[1][axis] - b[2][axis]) > 0.5]
            pos = sorted(b[1][1 - axis] for b in run)
            assert len(pos) >= 2, f"[spacing] {gp}: no bars along {'xy'[axis]}"
            gaps = [q - p_ for p_, q in zip(pos, pos[1:])]
            assert max(gaps) <= t["s"] + 1e-5 and min(gaps) > 1e-4, f"[spacing] {gp}: gaps {min(gaps):.3f}..{max(gaps):.3f} (s {t['s']})"
    _each(FOOTINGS[tn], one, "footings")

    # no two solids share volume (pits excluded); pits may overlap and are counted once
    solids = [(k, b) for (el, _), x in r.items() if el != "excavation" for k, b in enumerate(x["boxes"])]
    clash = [(a, b) for (_, a), (_, b) in itertools.combinations(solids, 2) if (i := _inter(a, b)) and _vol(i) > 1e-6]
    assert not clash, f"[clash] {len(clash)} solid pairs share volume"
    pits = g("excavation")["boxes"]
    assert not any(_inter(_inter(a, b) or a, c) for a, b, c in itertools.combinations(pits, 3) if _inter(a, b)), \
        "three pits overlap: pairwise check no longer valid"
    pair = sum(_vol(i) for a, b in itertools.combinations(pits, 2) if (i := _inter(a, b)))
    eq(_union_volume(pits), sum(_vol(b) for b in pits) - pair, "net excavation")
    msg = f"ST01 ok: {n} footings, {nb}+{nb} bars each, net pit {_union_volume(pits):.3f} m³"
    st = bpy.data.collections.get(C_STUB)
    if st and st.objects:
        msg += " | " + _check_stubs(r)
        gb = bpy.data.collections.get(C_GB)
        if gb and gb.objects:
            before = {**r, **qto(C_STUB)}
            msg += " | " + _check_beams(before)
            fl = bpy.data.collections.get(globals().get("C_FLOOR", ""))
            if fl and fl.objects:
                before = {**before, **qto(C_GB)}
                msg += " | " + _check_floor(before)
                cc = bpy.data.collections.get(globals().get("C_COL", ""))
                if cc and cc.objects:
                    before = {**before, **qto(C_FLOOR)}
                    msg += " | " + _check_columns(before)
                    cw = bpy.data.collections.get(globals().get("C_WALL", ""))
                    if cw and cw.objects:
                        before = {**before, **qto(C_COL)}
                        msg += " | " + _check_walls(before)
                        cr = bpy.data.collections.get(globals().get("C_ROOF", ""))
                        if cr and cr.objects:
                            before = {**before, **qto(C_WALL)}
                            msg += " | " + _check_roof(before)
                            cv = bpy.data.collections.get(globals().get("C_COVER", ""))
                            if cv and cv.objects:
                                msg += " | " + _check_cover(before)
                                ce = bpy.data.collections.get(globals().get("C_CEIL", ""))
                                if ce and ce.objects:
                                    msg += " | " + _check_ceilings({**before, **qto(C_COVER)})
                                    ct = bpy.data.collections.get(globals().get("C_TILE", ""))
                                    if ct and ct.objects:
                                        msg += " | " + _check_tiles(before)
                                    cp = bpy.data.collections.get(globals().get("C_PAINT", ""))
                                    if cp and cp.objects:
                                        msg += " | " + _check_paint(before)
                                    cel = bpy.data.collections.get(globals().get("C_ELEC", ""))
                                    if cel and cel.objects:
                                        msg += " | " + _check_elec(before)
                                    cco = bpy.data.collections.get(globals().get("C_COND", ""))
                                    if cco and cco.objects:
                                        msg += " | " + _check_conduit(before)
                                    cun = bpy.data.collections.get(globals().get("C_UNIT", ""))
                                    if cun and cun.objects:
                                        msg += " | " + _check_units(before)
                                    csn = bpy.data.collections.get(globals().get("C_SAN", ""))
                                    if csn and csn.objects:
                                        msg += " | " + _check_sanitary(before)
                                    cex = bpy.data.collections.get(globals().get("C_EXTRA", ""))
                                    if cex and cex.objects:
                                        msg += " | " + _check_extras(before)
    return msg


def _check_stubs(rf):
    """ST02 against the spec (STUBS, STUB_TOP, GB_TOP, FOOT_BOT), reading only the model; rf = ST01 rows."""
    def eq(a, b, what):
        assert abs(a - b) <= 1e-5 * max(abs(b), 1e-9), f"[{what}] model {a:.6f} != expected {b:.6f}"
    r, lv = qto(C_STUB), _stub_levels()
    f1 = TYPES["F1"]
    zb0, mat_top = FOOT_BOT + f1["T"], FOOT_BOT + f1["bottom"] + 2 * f1["d"]
    out = []
    for sn, t in STUBS.items():
        gs = STUB_GRIDS[sn]
        assert all(abs(lv[g][1] - STUB_TOP) < 1e-9 for g in gs), f"[level] stub top from GB_LINES != A-10/A-11 {STUB_TOP}"
        g_ = lambda el: r.get((el, sn)) or dict(n=0, vol=0.0, side=0.0, bars=[])
        n, H = len(gs), STUB_TOP - zb0
        for el in ("concrete", "rebar", "ties"):
            assert g_(el)["n"] == n, f"[count] stub {el}: {g_(el)['n']} objects, {n} stubs"
        eq(g_("concrete")["vol"], n * t["b"] ** 2 * H, "stub concrete")
        eq(g_("concrete")["side"], n * 4 * t["b"] * H, "stub formwork")
        a, m = t["b"] / 2 - t["cover"] - t["dt"] / 2, t["b"] / 2 - t["cover"] - t["dt"] - t["d"] / 2
        top, zf = GB_TOP + t["lap"], mat_top + t["d"] / 2
        Lbar = top - zf + t["foot"]
        eq(sum(g_("rebar")["bars"]), n * t["nbar"] * Lbar, "rebar length")
        objs = {o.name: o for o in _coll(C_STUB).objects}
        foot = {o.parent["grid"]: o for o in _coll(C_FOOT).objects if o.name.endswith("_Conc") and o.parent}
        x_ties = [0]

        def one(gp):
            x, y = GX[gp[1:]], GY[gp[0]]
            assert f"{sn}_{gp}" in objs, f"[count] {gp}: no stub"
            bm = _world_bm(objs[f"{sn}_{gp}_Conc"])
            try:
                c = _obj_boxes(bm, "stub")[0]
            finally:
                bm.free()
            w = t["b"] / 2
            assert max(abs(c[0] - (x - w)), abs(c[3] - (x + w)), abs(c[1] - (y - w)), abs(c[4] - (y + w))) < 1e-5, \
                f"[position] {gp}: stub not centred on its grid point"
            assert abs(c[2] - zb0) < 1e-5 and abs(c[5] - STUB_TOP) < 1e-5, f"[level] {gp}: stub z {c[2]:.3f}..{c[5]:.3f}"
            bars = _world_bars(objs[f"{sn}_{gp}_Bars"])
            assert len(bars) == t["nbar"], f"[bars] {gp}: {len(bars)} starters, S-03 has {t['nbar']}"
            ver = sorted((round(b[-1].x - x, 4), round(b[-1].y - y, 4)) for b in bars)
            want = sorted({(sx * m, sy * m) for sx in (-1, 1) for sy in (-1, 1)} |
                          ({(0.0, -m), (0.0, m)} if t["nbar"] == 6 else set()))
            assert all(abs(p[0] - q[0]) < 1e-4 and abs(p[1] - q[1]) < 1e-4 for p, q in zip(ver, want)), \
                f"[cover] {gp}: starters not tight inside the {t['cover']} cover"
            for b in bars:
                assert len(b) == 3 and abs(b[0].z - zf) < 1e-5 and abs(b[1].z - zf) < 1e-5, \
                    f"[starter] {gp}: foot not on the mat (z {b[0].z:.3f}, mat top {mat_top:.3f})"
                assert abs((b[0] - b[1]).length - t["foot"]) < 1e-5, f"[starter] {gp}: L-foot {(b[0] - b[1]).length:.3f}"
                assert abs(b[2].z - top) < 1e-5, f"[starter] {gp}: top {b[2].z:.3f} != beam top + lap {top:.3f}"
                assert abs(b[1].x - b[2].x) < 1e-6 and abs(b[1].y - b[2].y) < 1e-6, f"[starter] {gp}: bar not vertical"
                fc = foot.get(gp)
                assert fc, f"[count] {gp}: no footing under the stub"
                bm = _world_bm(fc)
                try:
                    fb = _obj_boxes(bm, "foot")[0]
                finally:
                    bm.free()
                assert all(fb[i] + f1["side"] - 1e-5 <= b[0][i] - t["d"] / 2 and b[0][i] + t["d"] / 2 <= fb[i + 3] - f1["side"] + 1e-5
                           for i in (0, 1)), f"[starter] {gp}: L-foot outside the footing"
            ties = _world_bars(objs[f"{sn}_{gp}_Ties"])
            zs = sorted(tb[0].z - c[2] for tb in ties)
            assert len(zs) >= 2 and abs(zs[0] - t["first"]) < 1e-5 and abs(zs[-1] - (H - t["first"])) < 1e-5, \
                f"[spacing] {gp}: ties {zs[0]:.3f}..{zs[-1]:.3f} not {t['first']} from the stub ends"
            gaps = [q - p for p, q in zip(zs, zs[1:])]
            assert max(gaps) <= t["s"] + 1e-5 and min(gaps) > 1e-4, f"[spacing] {gp}: tie gaps {min(gaps):.3f}..{max(gaps):.3f} (s {t['s']})"
            for tb in ties:
                hx = max(abs(p.x - x) for p in tb)
                assert abs(hx - a) < 1e-5, f"[cover] {gp}: tie half-size {hx:.4f} != {a:.4f} (cover {t['cover']})"
            x_ties[0] += len(ties) * (8 * a + 2 * t["hook"])
        _each(gs, one, "stubs")
        eq(sum(g_("ties")["bars"]), x_ties[0], "tie length")
        out.append(f"{n} stubs {t['b']:.2f}×{t['b']:.2f} H {H:.2f}, {t['nbar']} starters {Lbar:.3f} m, "
                   f"{len(_world_bars(objs[f'{sn}_{gs[0]}_Ties']))} ties each")
    # stubs share no volume with footings or each other
    solids = [b for (el, _), x in list(rf.items()) + list(r.items()) if el != "excavation" for b in x["boxes"]]
    clash = [(a, b) for a, b in itertools.combinations(solids, 2) if (i := _inter(a, b)) and _vol(i) > 1e-6]
    assert not clash, f"[clash] {len(clash)} solid pairs share volume (stubs/footings)"
    return "ST02 ok: " + "; ".join(out)
