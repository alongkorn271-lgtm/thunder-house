"""KK01 ST06 ผนังก่ออิฐ + เสาเอ็น/ทับหลัง + ฉาบปูน – exec'd after kk01_cols.py (kk01_load.py).

A-02: every wall "ผนังก่ออิฐมอญครึ่งแผ่น ฉาบปูนเรียบ" (types 1–4 differ only in the finish: paint / tile / wood
cladding, a later stage). Lines and openings read off A-04, sizes off A-14 / A-15 (WALLS, OPENINGS).
  Brick 3.5 × 7 × 16 cm, wall 0.07, joints 1 cm → 1 / (0.17 × 0.045) bricks/m² + 5 % (assumed, common อิฐมอญ).
  Exterior walls flush with the column face (practice), interior walls on the grid line. Wall base = the floor under
  it (+0.77 topping, +0.67 bare beam top), top = the column top of its zone (+4.175 house, +3.175 lean-to rows A/B).
  Openings from the finished floor (base + FINISH): windows sill + FINISH, doors from the structure to FINISH + height.
  Concrete ties 0.10 × wall (2-RB6, assumed): a tie column at every jamb, at every wall end without a column, and
  so no brick panel is longer than 2.50 m; a lintel over every opening, a sill under every window, a band at
  base + 2.30 on walls over 3 m; brick slivers (< 0.20 long or < 0.10 high) become concrete (practice).
  Plaster 1.5 cm on both faces, reveals and every exposed column face (skins cut by the solids they meet); a skin
  over a bare beam top beside the topping (the wet side, ST04 `_wet_cuts`) runs down to the beam top.
Objects: WL_<a>-<b> (_Brick, _Tie, _TieBars, _Open [wire, take-off only]), PL_Walls (_Plaster). Spec: ST06_walls_spec.md.
"""

BRICK = dict(t=0.07, l=0.16, h=0.035, joint=0.01, waste=0.05, name="อิฐมอญ 3.5×7×16 ซม.")
TIE = dict(w=0.10, d=0.006, n=2, cover=0.02, panel=2.50, band=2.30, band_min_h=3.0, sliver_u=0.20, sliver_z=0.10,
           grade="St.180 ksc", bar="RB6 SR24")
PLASTER = dict(t=0.015)
UNIT_GAP = 0.005             # ST14 (practice): A-14 / A-15 sizes are the units' overall frame; brick = unit + (gap + plaster) a side


def _ug():
    return UNIT_GAP + PLASTER["t"]
OPENINGS = {"D1": (1.80, 2.15, 0.0), "D2": (1.00, 2.00, 0.0), "D3": (0.90, 2.00, 0.0), "D4": (0.80, 2.05, 0.0),
            "W1": (2.40, 1.20, 0.90), "W2": (1.40, 1.20, 0.90), "W3": (1.00, 1.90, 0.20), "W4": (0.60, 1.55, 0.50),
            "W5": (0.80, 0.50, 1.80), "W6": (2.60, 1.20, 0.90)}          # (width, height, sill) A-14 / A-15
OPENING_COUNT = {"D1": 1, "D2": 2, "D3": 5, "D4": 2, "W1": 2, "W2": 3, "W3": 2, "W4": 6, "W5": 2, "W6": 1}   # A-04
# (from, to, flush side across the line: +1 / −1 exterior, 0 interior centred, lean-to?, [(opening, centre along)])
WALLS = [
    ("A2", "A5", +1, True, [("W1", 8.06)]),
    ("A2", "B2", -1, True, [("W6", 10.70)]),
    ("A5", "B5", +1, True, [("D2", 11.48)]),
    ("B2", "B5", -1, True, [("D2", 8.81)]),
    ("C1", "C6", +1, False, [("W2", 1.76), ("W1", 6.78), ("D3", 8.80), ("W2", 11.26)]),
    ("C1", "G1", -1, False, [("W4", 7.00), ("W4", 4.52), ("W5", 3.16)]),
    ("E1", "E1a", 0, False, []),
    ("E1a", "Gb1a", 0, False, [("D4", 2.985)]),          # ST14: 2.95 → 2.985 (the unit's opening, +2 cm a side, met the side wall)
    ("Gb1", "Gb1a", 0, False, []),
    ("E2", "G2", 0, False, []),
    ("E2", "E3", 0, False, []),
    ("C3", "G3", 0, False, [("D3", 6.95), ("D3", 3.40)]),
    ("Ga3", "Ga5", -1, False, [("D1", 6.00), ("W2", 8.12)]),
    ("G1", "G3", -1, False, [("W3", 2.50)]),
    ("C5", "G5", 0, False, [("D3", 5.20), ("D3", 2.43)]),
    ("D5", "D6", 0, False, [("D4", 10.89)]),
    ("F5", "F6", 0, False, []),
    ("C6", "G6", +1, False, [("W4", 6.93), ("W4", 5.02), ("W5", 3.70), ("W4", 2.55), ("W4", 0.80)]),
    ("G5", "G6", -1, False, [("W3", 11.26)]),
]
C_WALL = "KK01 ST06 Walls"
STAGES.append(C_WALL)


def _wl(w):
    """(name, ax, kc (wall centre across), u0, u1 (grid), flush, lean, openings, k (grid line), a, b)."""
    a, b, flush, lean, ops = w
    (xa, ya), (xb, yb) = _pxy(a), _pxy(b)
    assert (xa == xb) != (ya == yb), f"wall {a}-{b} not along a grid line"
    ax = 0 if ya == yb else 1
    k = (ya, xa)[ax]
    kc = k + flush * (COL["b"] / 2 - BRICK["t"] / 2)
    (u0, pa), (u1, pb) = sorted((((xa, ya)[ax], a), ((xb, yb)[ax], b)))
    return f"{a}-{b}", ax, kc, u0, u1, flush, lean, ops, k, pa, pb


def _col_prisms():
    out = {}
    for gs in STUB_GRIDS.values():
        for g in gs:
            x, y = _pxy(g)
            w = COL["b"] / 2
            out[g] = (x - w, y - w, GB_TOP, x + w, y + w, _col_top(g))
    return out


def _wall_top(lean):
    return COL_TOP_LEAN if lean else COL_TOP_MAIN


def _box(ax, u0, u1, v0, v1, z0, z1):
    return (u0, v0, z0, u1, v1, z1) if ax == 0 else (v0, u0, z0, v1, u1, z1)


def _walls_on_beams():
    for w in WALLS:
        name, ax, kc, u0, u1, flush, lean, ops, k, *_ = _wl(w)
        assert _edge_on_beams(ax, k, u0, u1), f"[beams] wall {name} has no ground beam under all of it"


def _wall_ends(lines):
    """u extent of every wall: to the column centre ± b/2, or to the far face of the wall it ends on."""
    stubs = {g for gs in STUB_GRIDS.values() for g in gs}
    out = {}
    for name, ax, kc, u0, u1, flush, lean, ops, k, pa, pb in lines:
        ends = []
        for u, p, sgn in ((u0, pa, -1), (u1, pb, +1)):
            if p in stubs:
                ends.append(u + sgn * COL["b"] / 2)
                continue
            other = [l for l in lines if l[1] != ax and abs(l[8] - u) < 1e-9 and l[3] - 1e-9 <= k <= l[4] + 1e-9]
            assert other, f"wall {name}: end {p} meets neither a column nor a wall"
            ends.append(other[0][2] + sgn * BRICK["t"] / 2)
        out[name] = tuple(ends)
    return out


def _tees(line, lines):
    """Across-positions where another wall ends on this one between its ends (lateral support)."""
    name, ax, kc, u0, u1, flush, lean, ops, k, *_ = line
    return [l[2] for l in lines if l[1] != ax and (abs(l[3] - k) < 1e-9 or abs(l[4] - k) < 1e-9) and u0 + 1e-9 < l[8] < u1 - 1e-9]


def _wall_layout():
    """Everything the walls are made of, in world boxes: per wall dict(env, open, ties, bars) + plaster boxes."""
    _walls_on_beams()
    lines = [_wl(w) for w in WALLS]
    ends = _wall_ends(lines)
    cols = _col_prisms()
    fp = _footprint()
    t, T = BRICK["t"], TIE
    placed, out = [], {}
    col_list = list(cols.values())
    for line in lines:
        name, ax, kc, u0, u1, flush, lean, ops, k, *_ = line
        e0, e1 = ends[name]
        v0, v1 = kc - t / 2, kc + t / 2
        top = _wall_top(lean)
        raw2 = (*_box(ax, e0, e1, v0, v1, 0.0, 1.0),)
        outside = [q for q in _cut(raw2, fp) if q[ax + 3] - q[ax] > 1e-6]
        inside = _cut(raw2, outside) if outside else [raw2]           # whole-thickness pieces (fp is sliced)
        face_env = [(*q[:2], TOPPING["top"], *q[3:5], top) for q in inside] + [(*q[:2], GB_TOP, *q[3:5], top) for q in outside]
        env = [p for b in face_env for p in _cut(b, col_list + placed)]
        placed += env
        base_at = lambda u: min((b[2] for b in env if b[ax] - 1e-6 <= u <= b[ax + 3] + 1e-6), default=TOPPING["top"])
        # vertical supports along u: column faces on the line, junctions, jamb ties
        sup = [(c[ax], c[ax + 3]) for c in col_list if c[1 - ax] - 1e-6 <= kc <= c[4 - ax] + 1e-6 and c[ax + 3] > e0 - 1e-6 and c[ax] < e1 + 1e-6]
        vties, openings = [], []
        for u_end, sgn in ((e0, 1), (e1, -1)):                          # wall end without a column: tie there
            if not any(a_ - 1e-6 <= u_end - sgn * 1e-4 <= b_ + 1e-6 for a_, b_ in sup):
                vties.append((u_end, u_end + sgn * T["w"]) if sgn > 0 else (u_end - T["w"], u_end))
        for c_ in _tees(line, lines):            # a wall ending on this one: support + a tie column at the junction
            sup.append((c_ - t / 2, c_ + t / 2))
            if not any(a_ - 1e-6 <= c_ <= b_ + 1e-6 for a_, b_ in sup[:-1]):
                vties.append((c_ - T["w"] / 2, c_ + T["w"] / 2))
        for tp, c in ops:
            w_, h_, sill = OPENINGS[tp]
            a_, b_ = c - w_ / 2 - _ug(), c + w_ / 2 + _ug()
            for c0, c1 in sup:                                  # ST14: widened onto a column → slid off it (flagged in spec)
                if a_ < c1 - 1e-6 and b_ > c1 and a_ > c0 - 1e-6:
                    a_, b_ = c1, c1 + (b_ - a_)
                elif b_ > c0 + 1e-6 and a_ < c0 and b_ < c1 + 1e-6:
                    a_, b_ = c0 - (b_ - a_), c0
            assert e0 - 1e-6 <= a_ and b_ <= e1 + 1e-6, f"wall {name}: {tp} at {c} outside the wall"
            base = base_at(c)
            z0 = base + FINISH + sill - _ug() if sill > 1e-9 else base    # a door from the structure, under the finish
            openings.append((tp, _box(ax, a_, b_, v0, v1, z0, base + FINISH + sill + h_ + _ug())))
            for j0, j1 in ((a_ - T["w"], a_), (b_, b_ + T["w"])):
                if not any(s0 - 1e-6 <= j0 + 1e-4 and j1 - 1e-4 <= s1 + 1e-6 for s0, s1 in sup):
                    vties.append((j0, j1))
        # panels longer than T["panel"]: ties evenly between supports
        stops = sorted(sup + vties + [(e0 - 1, e0), (e1, e1 + 1)])
        for (p0, p1), (q0, q1) in zip(stops, stops[1:]):
            L = q0 - p1
            if L > T["panel"] + 1e-9:
                n = math.ceil((L + T["w"]) / (T["panel"] + T["w"]) - 1e-9)    # n panels, n − 1 ties
                s_ = (L - (n - 1) * T["w"]) / n
                for i in range(1, n):
                    j0 = p1 + i * s_ + (i - 1) * T["w"]
                    vties.append((j0, j0 + T["w"]))
        ties = []
        for j0, j1 in vties:
            j0, j1 = max(j0, e0), min(j1, e1)
            ties += [(*_box(ax, j0, j1, v0, v1, base_at((j0 + j1) / 2), top),)]
        h_wall = top - base_at((e0 + e1) / 2)
        bands = []
        if h_wall > T["band_min_h"] + 1e-9:
            zb = base_at((e0 + e1) / 2) + T["band"]
            bands.append(_box(ax, e0, e1, v0, v1, zb, zb + T["w"]))
        for tp, ob in openings:
            a_, b_ = ob[ax] - T["w"], ob[ax + 3] + T["w"]
            if not bands or abs(ob[5] - bands[0][2]) > 1e-6:
                bands.append(_box(ax, a_, b_, v0, v1, ob[5], ob[5] + T["w"]))          # lintel
            if OPENINGS[tp][2] > 1e-9:
                bands.append(_box(ax, a_, b_, v0, v1, ob[2] - T["w"], ob[2]))          # sill
        conc = []
        for b in ties + bands:
            conc += [q for e in env for i in [_inter(b, e)] if i for q in _cut(i, conc + [o for _, o in openings])]
        bricks = [q for e in env for q in _cut(e, conc + [o for _, o in openings])]
        # slivers to concrete
        sl = [b for b in bricks if b[ax + 3] - b[ax] < T["sliver_u"] - 1e-6 or b[5] - b[2] < T["sliver_z"] - 1e-6]
        bricks = [b for b in bricks if b not in sl]
        conc += sl
        out[name] = dict(ax=ax, kc=kc, env=env, face_env=face_env, open=openings, conc=conc, brick=bricks, lean=lean, flush=flush, ends=(e0, e1))
    return out, cols


def _tie_bars(ax, boxes):
    """2-RB6 along the long axis of every concrete tie piece (vertical in tie columns, horizontal in bands)."""
    T, bars = TIE, []
    for b in boxes:
        dims = [b[i + 3] - b[i] for i in range(3)]
        long = max(range(3), key=lambda i: dims[i])
        if dims[long] < 0.30:
            continue
        cv = T["cover"] + T["d"] / 2
        lo, hi = b[long] + cv, b[long + 3] - cv
        across = [i for i in range(3) if i != long]
        # two bars in the wall plane: spread along the larger of the two other dims
        sp = max(across, key=lambda i: dims[i])
        other = [i for i in across if i != sp][0]
        for s in (b[sp] + cv, b[sp + 3] - cv):
            p0, p1 = [0.0] * 3, [0.0] * 3
            p0[long], p1[long] = lo, hi
            p0[sp] = p1[sp] = s
            p0[other] = p1[other] = (b[other] + b[other + 3]) / 2
            bars.append([tuple(p0), tuple(p1)])
    return bars


def _above_ceiling_zones(wall_boxes):
    """Room volumes above their ceilings (ST09 ROOMS), traced from the brick/tie walls and the columns, with the
    column footprints taken out, disjoint: inside plaster stops at the ceiling there (practice), outside plaster and
    open spaces (verandahs, laundry) keep it to the wall top. [] while the ceiling stage is not loaded."""
    if "ROOMS" not in globals():
        return []
    cols = list(_col_prisms().values())
    obst = wall_boxes + cols
    out = []
    for name, seed, lvl, tp in ROOMS:
        r = _room_rect(seed, lvl - 0.05, obst)
        pcs = _rects_minus([r], [(c[0], c[1], c[3], c[4]) for c in cols])
        out += [(p[0], p[1], lvl, p[2], p[3], COL_TOP_MAIN + 1.0) for p in pcs]
    return _disjoint(out)


def _plaster_boxes(lay, cols):
    """Raw plaster boxes (faces, reveals, column skins), unioned and cut by every solid."""
    tp, t = PLASTER["t"], BRICK["t"]
    raw = []
    beams = [b for (el, _), x in qto(C_GB).items() if el == "concrete" for b in x["boxes"]] +         [b for (el, tp_), x in qto(C_FLOOR).items() if el == "concrete" and tp_ == "S" for b in x["boxes"]]   # + S slabs
    fp = _footprint()
    for name, d in lay.items():
        ax, kc = d["ax"], d["kc"]
        for e in d["face_env"]:   # the whole face; the cut by the solids takes columns and crossing walls out
            for v0, v1 in ((kc - t / 2 - tp, kc - t / 2), (kc + t / 2, kc + t / 2 + tp)):
                face = list(e)
                face[1 - ax], face[4 - ax] = v0, v1
                face = tuple(face)
                pieces = [face]
                if face[2] > GB_TOP + 1e-6:   # on the topping: where the skin stands over a bare beam / S slab top, down to it
                    low = [(*i[:2], GB_TOP, *i[3:5], face[5]) for bb in beams
                           if (i := _inter((*face[:2], 0.0, *face[3:5], 1.0), (*bb[:2], 0.0, *bb[3:5], 1.0)))]
                    low = [q for lw in low for q in _cut(lw, [(f[0], f[1], GB_TOP - 1, f[3], f[4], 99.0) for f in fp])]
                    low = [q for q in low if min(q[3] - q[0], q[4] - q[1]) > 1e-6]
                    pieces = _cut(face, low) + low
                cutters = [_grow_across((*o[:2], GB_TOP - 1.0, *o[3:]) if OPENINGS[tp_][2] < 1e-9 else o, ax, tp)
                           for tp_, o in d["open"]]                      # no skin under a door (the riser goes there)
                for pc in pieces:
                    raw += _cut(pc, cutters)
        for tp_, o in d["open"]:
            a_, b_ = o[ax], o[ax + 3]
            vv0, vv1 = kc - t / 2 - tp, kc + t / 2 + tp
            raw.append(_box(ax, a_, a_ + tp, vv0, vv1, o[2], o[5]))
            raw.append(_box(ax, b_ - tp, b_, vv0, vv1, o[2], o[5]))
            raw.append(_box(ax, a_, b_, vv0, vv1, o[5] - tp, o[5]))
            if OPENINGS[tp_][2] > 1e-9:
                raw.append(_box(ax, a_, b_, vv0, vv1, o[2], o[2] + tp))
    for g, c in cols.items():
        top = c[5] - COL["pt"]
        x0, y0, z0, x1, y1 = c[0], c[1], c[2], c[3], c[4]
        raw += [(x0 - tp, y0 - tp, z0, x0, y1 + tp, top), (x1, y0 - tp, z0, x1 + tp, y1 + tp, top),
                (x0, y0 - tp, z0, x1, y0, top), (x0, y1, z0, x1, y1 + tp, top)]
    return raw


def _grow_across(o, ax, d):
    o = list(o)
    o[1 - ax] -= d
    o[4 - ax] += d
    return tuple(o)


def _all_solids(colls):
    out = []
    for cn in colls:
        for (el, _), x in qto(cn).items():
            if el not in ("excavation",):
                out += x["boxes"]
    return out


def _near(b, boxes, pad=1e-6):
    return [c for c in boxes if c[0] < b[3] + pad and c[3] > b[0] - pad and c[1] < b[4] + pad and c[4] > b[1] - pad
            and c[2] < b[5] + pad and c[5] > b[2] - pad]


def build_walls():
    """ST06: brick walls, concrete ties, opening voids, plaster."""
    lay, cols = _wall_layout()
    c = _clear(C_WALL)
    brick_m = mat("M_Brick", (0.62, 0.30, 0.20), 0.9)
    conc = mat("M_Concrete", (0.50, 0.50, 0.48), 0.85)
    steel = mat("M_Rebar", (0.28, 0.17, 0.11), 0.55, 0.6)
    pl_m = mat("M_Plaster", (0.86, 0.85, 0.82), 0.9)
    for name, d in lay.items():
        root = bpy.data.objects.new(f"WL_{name}", None)
        root.empty_display_type, root.empty_display_size = "PLAIN_AXES", 0.2
        root["line"], root["type"] = name, "WL"
        c.objects.link(root)
        parts = {"Brick": _boxes_data(f"WL_{name}_Brick", d["brick"], brick_m, element="brick", type="WL",
                                      th=f"ผนังก่ออิฐมอญครึ่งแผ่น ({BRICK['name']})", wall_t=BRICK["t"])}
        if d["conc"]:
            parts["Tie"] = _boxes_data(f"WL_{name}_Tie", d["conc"], conc, element="concrete", type="TIE", grade=TIE["grade"],
                                       th="คอนกรีตเสาเอ็น / ทับหลัง / ทับหลังกลางผนัง")
            tb = _tie_bars(d["ax"], d["conc"])
            if tb:
                parts["TieBars"] = _rebar_data(f"WL_{name}_TieBars", tb, TIE["d"], steel, element="rebar", type="TIE",
                                               th="เหล็กเสริมเสาเอ็น/ทับหลัง", bar=TIE["bar"], dia_mm=round(TIE["d"] * 1000))
        if d["open"]:
            parts["Open"] = _boxes_data(f"WL_{name}_Open", [o for _, o in d["open"]], None, element="opening",
                                        type="OPEN", th="ช่องเปิด", kinds=",".join(tp for tp, _ in d["open"]))
        for k, data in parts.items():
            ob = bpy.data.objects.new(f"WL_{name}_{k}", data)
            ob.parent = root
            c.objects.link(ob)
            if k == "Open":
                ob.display_type, ob.hide_render = "WIRE", True
    bpy.context.view_layer.update()
    # plaster: cut by every solid of every stage incl. the walls just built
    solids = _all_solids([C_FOOT, C_STUB, C_GB, C_FLOOR, C_COL]) + \
        [b for d in lay.values() for b in d["brick"] + d["conc"]]
    raw = _plaster_boxes(lay, cols)
    tp = PLASTER["t"]
    zones = [(z[0] - tp, z[1] - tp, z[2], z[3] + tp, z[4] + tp, z[5])
             for z in _above_ceiling_zones([b for d in lay.values() for b in d["brick"] + d["conc"]])]
    pieces = []
    for b in raw:
        pieces += _cut(b, _near(b, solids) + _near(b, pieces) + _near(b, zones))
    pieces = [p for p in pieces if min(p[i + 3] - p[i] for i in range(3)) > 1e-5]
    root = bpy.data.objects.new("PL_Walls", None)
    c.objects.link(root)
    ob = bpy.data.objects.new("PL_Walls_Plaster", _boxes_data("PL_Walls_Plaster", pieces, pl_m, element="plaster",
                                                                type="PL", th=f"ฉาบปูนเรียบ หนา {PLASTER['t'] * 100:.1f} ซม."))
    ob.parent = root
    c.objects.link(ob)
    bpy.context.view_layer.update()
    return len(lay)


def walls_report():
    r = qto(C_WALL)
    out = []
    b = r[("brick", "WL")]
    area = b["vol"] / BRICK["t"]
    per = 1 / ((BRICK["l"] + BRICK["joint"]) * (BRICK["h"] + BRICK["joint"]))
    out.append(f"ผนังก่ออิฐมอญครึ่งแผ่น: {area:.2f} ตร.ม. (เนื้ออิฐ {b['vol']:.3f} ลบ.ม.) × {per:.1f} ก้อน/ตร.ม. + {BRICK['waste'] * 100:.0f} % "
               f"= {math.ceil(area * per * (1 + BRICK['waste'])):,} ก้อน")
    tc = r[("concrete", "TIE")]
    out.append(f"คอนกรีตเสาเอ็น/ทับหลัง: {tc['vol']:.3f} ลบ.ม. (≈ {tc['vol'] / (BRICK['t'] * TIE['w']):.1f} ม. ของหน้าตัด 0.07×0.10)")
    tb = r[("rebar", "TIE")]
    m = sum(tb["bars"])
    out.append(f"เหล็กเสาเอ็น/ทับหลัง {TIE['bar']}: {len(tb['bars'])} ท่อน = {m:.2f} ม. = {m * KG_M[6]:.1f} กก. → ใช้เหล็กเส้น 10 ม. {_stock_bars(tb['bars'])} เส้น")
    op = r[("opening", "OPEN")]
    kinds = {}
    for o in _coll(C_WALL).objects:
        if o.data and o.data.get("element") == "opening":
            for k in o.data["kinds"].split(","):
                kinds[k] = kinds.get(k, 0) + 1
    out.append("ช่องเปิด: " + " · ".join(f"{k} {v}" for k, v in sorted(kinds.items())) + f" = {sum(kinds.values())} ช่อง, {op['vol'] / BRICK['t']:.2f} ตร.ม.")
    p = r[("plaster", "PL")]
    out.append(f"ฉาบปูน: {p['vol'] / PLASTER['t']:.2f} ตร.ม. (ผนัง 2 ด้าน + ขอบช่องเปิด + ผิวเสา)")
    return "\n".join(out)


# ---------------------------------------------------------------- ST06 selfcheck

def _clashes(boxes, tol=1e-7):
    """Pairs of boxes sharing volume (sweep on x)."""
    bs = sorted(boxes, key=lambda b: b[0])
    out, active = [], []
    for b in bs:
        active = [a for a in active if a[3] > b[0] + 1e-9]
        for a in active:
            if (i := _inter(a, b)) and _vol(i) > tol and min(i[k + 3] - i[k] for k in range(3)) > 1e-5:   # float32 noise
                out.append((a, b))
        active.append(b)
    return out


def _check_walls(rows_before):
    def eq(a, b, what, rel=1e-5):
        assert abs(a - b) <= rel * max(abs(b), 1e-9), f"[{what}] model {a:.6f} != expected {b:.6f}"
    r = qto(C_WALL)
    objs = {o.name: o for o in _coll(C_WALL).objects}
    lines = [_wl(w) for w in WALLS]
    t, T, tp = BRICK["t"], TIE, PLASTER["t"]
    _walls_on_beams()
    cols = _col_prisms()

    def boxes(name):
        if name not in objs:
            return []
        bm = _world_bm(objs[name])
        try:
            return _obj_boxes(bm, name)
        finally:
            bm.free()
    # openings: counts by kind, sizes, sills above the floor under them
    floor_solids = _all_solids([C_GB, C_FLOOR])
    kinds = {}
    for name, ax, kc, u0, u1, flush, lean, ops, *_ in lines:
        ob = boxes(f"WL_{name}_Open")
        assert len(ob) == len(ops), f"[openings] wall {name}: {len(ob)} openings, A-04 has {len(ops)}"
        for tp_, c in ops:
            w_, h_, sill = OPENINGS[tp_]
            hit = [o for o in ob if abs((o[ax] + o[ax + 3]) / 2 - c) < 0.03]       # (ST14 may slide one off a column)
            assert hit, f"[openings] wall {name}: no {tp_} at {c}"
            o = hit[0]
            assert abs(o[ax + 3] - o[ax] - w_ - 2 * _ug()) < 1e-5 and abs(o[5] - o[2] - h_ - (FINISH + _ug() if sill < 1e-9 else 2 * _ug())) < 1e-5, \
                f"[openings] wall {name}: {tp_} {o[ax + 3] - o[ax]:.2f}×{o[5] - o[2]:.2f} != A-14/15 {w_}×{h_}"
            px, py = ((c, kc) if ax == 0 else (kc, c))
            base = max((q[5] for q in floor_solids if q[0] - 1e-6 <= px <= q[3] + 1e-6 and q[1] - 1e-6 <= py <= q[4] + 1e-6
                        and q[5] <= o[2] + 1e-5), default=None)
            assert base is not None, f"[openings] wall {name}: {tp_} over no floor"
            want = base + FINISH + sill - _ug() if sill > 1e-9 else base   # unit sills over the finished floor; doors from the structure
            assert abs(o[2] - want) < 1e-5, f"[openings] wall {name}: {tp_} sill {o[2] - base - FINISH:.3f} over the finish != {sill}"
            kinds[tp_] = kinds.get(tp_, 0) + 1
    assert kinds == OPENING_COUNT, f"[openings] counts {kinds} != A-04 {OPENING_COUNT}"
    under_solids = _all_solids([C_GB, C_FLOOR, C_COL])
    all_wall_pieces = [b for n in objs if n.endswith(("_Brick", "_Tie")) for b in boxes(n)]

    def wall(item):
        name, ax, kc, u0, u1, flush, lean, ops, *_ = item
        bk, tc = boxes(f"WL_{name}_Brick"), boxes(f"WL_{name}_Tie")
        allw = bk + tc + boxes(f"WL_{name}_Open")
        assert bk, f"[count] wall {name} missing"
        top = _wall_top(lean)
        for b in allw:
            assert abs(b[1 - ax] - (kc - t / 2)) < 1e-5 and abs(b[4 - ax] - (kc + t / 2)) < 1e-5, \
                f"[flush] wall {name}: piece at {b[1 - ax]:.3f}..{b[4 - ax]:.3f}, wall {kc - t / 2:.3f}..{kc + t / 2:.3f}"
            assert b[5] <= top + 1e-5, f"[level] wall {name}: piece above the wall top {top}"
        assert abs(max(b[5] for b in allw) - top) < 1e-5, f"[level] wall {name}: top {max(b[5] for b in allw):.3f} != {top}"
        if flush:   # exterior face on the column's outer face
            face = (kc + flush * t / 2)
            grid = kc - flush * (COL["b"] / 2 - t / 2)
            assert abs(face - (grid + flush * COL["b"] / 2)) < 1e-6, f"[flush] wall {name} not flush with the columns"
        # every bottom face rests on floor, beam or column
        for b in bk + tc:
            if b[2] > TOPPING["top"] + 1e-5:
                continue                                         # rests on wall pieces below: checked by the clash/fill
            fb = (b[0], b[1], b[2] - 0.005, b[3], b[4], b[2])
            on = sum(_vol(i) for q in _near(fb, under_solids) if (i := _inter(fb, q)))
            assert abs(on - _vol(fb)) < 1e-7, f"[level] wall {name}: piece at z {b[2]:.3f} not resting on the floor/beam"
        # supports: no brick panel longer than T['panel']; a tie beside every jamb unless a column is there
        for o in boxes(f"WL_{name}_Open"):
            for j0, j1 in ((o[ax] - T["w"], o[ax]), (o[ax + 3], o[ax + 3] + T["w"])):
                lo_, hi_ = min(b[ax] for b in allw), max(b[ax + 3] for b in allw)
                j0, j1 = max(j0, lo_), min(j1, hi_)
                if j1 - j0 < 1e-4:
                    continue
                probe = _box(ax, j0, j1, kc - 0.01, kc + 0.01, o[2], o[5])   # the full jamb strip must be concrete
                got = sum(_vol(i) for q in tc + list(cols.values()) if (i := _inter(probe, q)))
                ok = abs(got - _vol(probe)) < 1e-3 * _vol(probe)
                assert ok, f"[ties] wall {name}: no tie column beside an opening at {j0:.2f}"
        tees = _tees(item, lines)
        for q in bk:
            cuts = [q[ax]] + sorted(c_ for c_ in tees if q[ax] < c_ < q[ax + 3]) + [q[ax + 3]]
            longest = max(b_ - a_ for a_, b_ in zip(cuts, cuts[1:]))
            assert longest <= T["panel"] + t + 1e-5, f"[ties] wall {name}: brick panel {longest:.2f} m long"
            assert q[ax + 3] - q[ax] >= T["sliver_u"] - 1e-5 and q[5] - q[2] >= T["sliver_z"] - 1e-5, \
                f"[ties] wall {name}: brick sliver {q[ax + 3] - q[ax]:.3f} × {q[5] - q[2]:.3f}"
        if top - min(b[2] for b in allw) > T["band_min_h"] + 1e-9:
            zb = min(b[2] for b in allw) + T["band"]
            band = [q for q in tc if abs(q[2] - zb) < 1e-5 or (q[2] < zb + 1e-5 and q[5] > zb + T["w"] - 1e-5)]
            strip = _box(ax, -1e3, 1e3, kc - 1e-3, kc + 1e-3, zb, zb + T["w"])
            crossing = [q for q in all_wall_pieces if _inter(q, strip) and q not in bk + tc]   # another wall's end
            cover = sorted((q[ax], q[ax + 3]) for q in band + crossing + [c for c in cols.values()
                                                                             if c[1 - ax] - 1e-6 <= kc <= c[4 - ax] + 1e-6] +
                           boxes(f"WL_{name}_Open") if q[2] < zb + T["w"] + 1e-5 and q[5] > zb - 1e-5)
            u = min(b[ax] for b in allw)
            for a_, b_ in cover:
                if a_ <= u + 1e-5:
                    u = max(u, b_)
            assert u >= max(b[ax + 3] for b in allw) - 1e-5, f"[band] wall {name}: mid-height band broken at {u:.2f}"
    _each(lines, wall, "walls")
    # plaster covers every exposed vertical face of walls and columns above the floor, and nothing else is in it
    pl = boxes("PL_Walls_Plaster")
    assert pl and all(min(p[i + 3] - p[i] for i in (0, 1)) <= tp + 1e-5 or p[5] - p[2] <= tp + 1e-5 for p in pl), \
        "[plaster] a plaster piece thicker than the plaster"
    eq(max(min(p[i + 3] - p[i] for i in range(3)) for p in pl), tp, "plaster", 1e-3)
    wall_solids = [b for n in objs if n.endswith(("_Brick", "_Tie")) for b in boxes(n)]
    col_conc = [b for (el, _), x in qto(C_COL).items() if el == "concrete" for b in x["boxes"]]
    others = _all_solids([C_GB, C_FLOOR]) + [b for (el, _), x in qto(C_COL).items() if el == "plate" for b in x["boxes"]]
    zones = _above_ceiling_zones([b for n in objs if n.endswith(("_Brick", "_Tie")) for b in boxes(n)])
    others = others + zones            # faces of a room above its ceiling stay bare (inside plaster stops at the ceiling)
    pl_in_zone = [p for p in pl for z in _near(p, zones, -1e-4) if (i := _inter(p, z)) and _vol(i) > 1e-8]
    assert not pl_in_zone, f"[plaster] {len(pl_in_zone)} plaster pieces above a ceiling inside a room"
    sol = wall_solids + col_conc
    opens = [b for n in objs if n.endswith("_Open") for b in boxes(n)]
    exposed = covered = 0.0
    for b in sol:
        f = 2 * ((b[3] - b[0]) + (b[4] - b[1])) * (b[5] - b[2])
        f -= sum(_touch(b, q) for q in _near(b, sol + others) if q is not b)
        exposed += f
        covered += sum(_touch(b, q) for q in _near(b, pl))
    eq(covered, exposed, "plaster", 3e-4)   # mm slivers at column corners / the 6 mm plate step at column tops
    for o in opens:   # an opening stays open, minus its reveal plaster
        oax = 1 if abs(o[3] - o[0] - t) < 1e-5 else 0                     # wall along y: thickness in x
        inner = list(o)
        inner[oax], inner[oax + 3] = o[oax] + tp + 1e-4, o[oax + 3] - tp - 1e-4
        inner[1 - oax], inner[4 - oax] = o[1 - oax] + 1e-4, o[4 - oax] - 1e-4
        inner[2], inner[5] = o[2] + tp + 1e-4, o[5] - tp - 1e-4
        inner = tuple(inner)
        fill = [q for q in _near(inner, sol + pl) if _inter(inner, q)]
        assert not fill, f"[openings] something fills the opening {tuple(round(v, 3) for v in o)}: {tuple(round(v, 3) for v in fill[0])}"
    solids = [bx for rows in (rows_before,) for (el, _), x in rows.items() if el != "excavation" for bx in x["boxes"]] + \
        wall_solids + pl
    cl = _clashes(solids)
    assert not cl, f"[clash] {len(cl)} solid pairs share volume (walls / plaster vs the rest): {cl[0]}"
    return f"ST06 ok: {len(lines)} walls, {sum(kinds.values())} openings, brick {r[('brick', 'WL')]['vol'] / t:.1f} m², " \
           f"plaster {r[('plaster', 'PL')]['vol'] / tp:.1f} m²"
