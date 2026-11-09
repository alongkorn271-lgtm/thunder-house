"""KK01 ST03 คานคอดิน (ground beams) – exec'd after kk01_struct.py into the same namespace (kk01_load.py).

Beams = GB_LINES spans (S-02), grouped into runs (maximal collinear chains of spans). One root empty GB_<run> at the
run's start point, beam top level, children: _Conc (one box per clear span between joint faces), _Lean, _Sand (strips
`pad` wider than the beam; strips along y give way to strips along x), _Bars, _Stirrups. Joints J1_<point> (0.20 ×
0.20, beam bottom → beam top) at every span end, cast with the beams; a joint without a stub has its own lean and sand
square under it. Numbers: Construction/ST03_ground_beams_spec.md.
"""


def _gb_runs():
    """[dict(name, ax, o (start xy), top, G (length), nodes [(u, point)], spans [(u0, u1, type)])]."""
    for a, b, top, tp in GB_LINES:
        assert tp in BEAM_TYPES and abs(top - GB_TOP) < 1e-9, f"span {a}-{b}: type {tp} / top {top}"
    pts = {p for a, b, *_ in GB_LINES for p in (a, b)}
    for a, b, *_ in GB_LINES:   # a span runs node to node: no other node strictly inside it
        inside = [p for p in pts if p not in (a, b) and _on_span(p, a, b)]
        assert not inside, f"span {a}-{b} passes node(s) {inside}: split it there"
    keyed = {}
    for a, b, top, tp in GB_LINES:
        (xa, ya), (xb, yb) = _pxy(a), _pxy(b)
        ax = 0 if ya == yb else 1
        if (xa, ya)[ax] > (xb, yb)[ax]:
            a, b, xa, ya, xb, yb = b, a, xb, yb, xa, ya
        keyed.setdefault((ax, (xa, ya)[1 - ax]), []).append(((xa, ya)[ax], (xb, yb)[ax], a, b, top, tp))
    runs = []
    for (ax, k), sp in sorted(keyed.items()):
        sp.sort()
        chains = []
        for s in sp:
            if chains and abs(chains[-1][-1][1] - s[0]) < 1e-9:
                chains[-1].append(s)
            else:
                assert not chains or s[0] > chains[-1][-1][1] + 1e-9, f"spans overlap on line {'yx'[ax]}={k}"
                chains.append([s])
        for ch in chains:
            u0 = ch[0][0]
            o = (u0, k) if ax == 0 else (k, u0)
            nodes = [(0.0, ch[0][2])] + [(s[1] - u0, s[3]) for s in ch]
            runs.append(dict(name=f"{ch[0][2]}-{ch[-1][3]}", ax=ax, o=o, top=ch[0][4], G=ch[-1][1] - u0, nodes=nodes,
                             spans=[(s[0] - u0, s[1] - u0, s[5]) for s in ch]))
    stubs = {g for gs in STUB_GRIDS.values() for g in gs}
    ends = [p for r in runs for p in (r["nodes"][0][1], r["nodes"][-1][1])]
    for p in ends:   # a run ends on a stub or on another run (a beam on a beam)
        assert p in stubs or sum(any(q == p for _, q in r["nodes"]) for r in runs) >= 2, f"beam end {p} rests on nothing"
    assert stubs <= pts, f"stubs without a beam: {sorted(stubs - pts)}"
    return runs


def _gb_nodes():
    """point -> (joint bottom, joint top, width) for every span end."""
    stubs = {g: STUBS[sn]["b"] for sn, gs in STUB_GRIDS.items() for g in gs}
    out = {}
    for p in {p for a, b, *_ in GB_LINES for p in (a, b)}:
        tb = _tops_at(p)
        out[p] = (min(b for _, b in tb), max(t for t, _ in tb), stubs.get(p, GBEAM["b"]))
    return out


def _pt(ax, u, v, z):
    return (u, v, z) if ax == 0 else (v, u, z)


def _uv(ax, u0, v0, z0, u1, v1, z1):
    return (*_pt(ax, u0, v0, z0), *_pt(ax, u1, v1, z1))


def _clear_spans(run, jb):
    return [(u0 + jb[run["nodes"][i][1]] / 2, u1 - jb[run["nodes"][i + 1][1]] / 2, tp)
            for i, (u0, u1, tp) in enumerate(run["spans"])]


def _gb_strips(runs, jb):
    """[(run name, world box)] lean footprint (b + 2 pad) under every clear span, z = beam bottom − lean .. bottom."""
    t, w = GBEAM, GBEAM["b"] / 2 + GBEAM["pad"]
    out = []
    for r in runs:
        o, ax, zb = r["o"], r["ax"], r["top"] - t["h"]
        for s0, s1, _ in _clear_spans(r, jb):
            out.append((r["name"], _uv(ax, o[ax] + s0, o[1 - ax] - w, zb - t["lean"], o[ax] + s1, o[1 - ax] + w, zb)))
    return out


def _gb_squares(nodes):
    """Lean squares under joints without a stub."""
    stubs = {g for gs in STUB_GRIDS.values() for g in gs}
    t = GBEAM
    return {p: (x - w / 2, y - w / 2, zb0 - t["lean"], x + w / 2, y + w / 2, zb0)
            for p, (zb0, _, w) in nodes.items() if p not in stubs for x, y in (_pxy(p),)}


def _box_minus(a, c):
    """a minus c as disjoint boxes (no sliver under 1 µm)."""
    i = _inter(a, c)
    if not i or min(i[k + 3] - i[k] for k in range(3)) < 1e-6:
        return [a]
    out, lo, hi = [], list(a[:3]), list(a[3:])
    for k in range(3):
        if lo[k] < i[k] - 1e-6:
            b = lo + hi
            b[k + 3] = i[k]
            out.append(tuple(b))
            lo[k] = i[k]
        if i[k + 3] < hi[k] - 1e-6:
            b = lo + hi
            b[k] = i[k + 3]
            out.append(tuple(b))
            hi[k] = i[k + 3]
    return out


def _lap_pieces(a, b, cands, hook):
    """Pieces (u0, u1, hook at start, hook at end) of a bar a..b hooked at both ends, each ≤ STOCK; laps `lap`
    centred on a candidate point, the first piece as long as stock allows (greedy)."""
    lap, out, s, hs = GBEAM["lap"], [], a, True
    while (b - s) + hook * hs + hook > STOCK + 1e-9:
        ok = [c for c in cands if c - lap / 2 > s + 1e-9 and c + lap / 2 < b - 1e-9 and
              c + lap / 2 - s + hook * hs <= STOCK + 1e-9]
        assert ok, f"no lap position for a bar {a:.2f}..{b:.2f}"
        c = max(ok)
        out.append((s, c + lap / 2, hs, False))
        s, hs = c - lap / 2, False
    return out + [(s, b, hs, True)]


def _vs(n, eb):
    """Across-beam positions of n bars between the two corner bars."""
    return [(eb - GBEAM["b"] / 2) * (1 - 2 * (j + 1) / (n + 1)) for j in range(n)]


def _beam_bars(r, jb):
    """Bars (point lists, local to the run root) of one run."""
    t, ax, G, nodes = GBEAM, r["ax"], r["G"], r["nodes"]
    eb = t["cover"] + t["dt"] + t["d"] / 2
    h = t["h"]
    assert 2 * t["hook"] <= h - 2 * eb + 1e-9, "top and bottom bar hooks overlap"
    ea, ez = jb[nodes[0][1]] / 2 - eb, G + jb[nodes[-1][1]] / 2 - eb    # bar ends inside the end joints
    cc = [u for u, _ in nodes]
    mids = [(u0 + u1) / 2 for u0, u1, _ in r["spans"]]
    bars = []
    for z, dz, cands in ((-eb, -t["hook"], mids), (eb - h, t["hook"], cc[1:-1])):   # top: lap mid-span, bottom: over a support
        for v in (eb - t["b"] / 2, t["b"] / 2 - eb):
            for u0, u1, hs, he in _lap_pieces(-ea, ez, cands, t["hook"]):
                bars.append(([_pt(ax, u0, v, z + dz)] if hs else []) + [_pt(ax, u0, v, z), _pt(ax, u1, v, z)] +
                            ([_pt(ax, u1, v, z + dz)] if he else []))
    for i, (u0, u1, tp) in enumerate(r["spans"]):
        bt = BEAM_TYPES[tp]
        a0, a1 = u0 - (jb[nodes[i][1]] / 2 - eb), u1 + (jb[nodes[i + 1][1]] / 2 - eb)
        bars += [[_pt(ax, a0, v, eb - h), _pt(ax, a1, v, eb - h)] for v in _vs(bt["extra"], eb)]   # B1 3rd bottom bar
        L = u1 - u0
        bars += [[_pt(ax, (u0 + u1 - t["mid"] * L) / 2, v, eb - h), _pt(ax, (u0 + u1 + t["mid"] * L) / 2, v, eb - h)]
                 for v in _vs(bt["nsp"], eb)]                                # special bottom bars, mid-span
    for i, u in enumerate(cc):                                              # special top bars over every support
        adj = [r["spans"][j][2] for j in (i - 1, i) if 0 <= j < len(r["spans"])]
        for v in _vs(max(BEAM_TYPES[tp]["nsp"] for tp in adj), eb):
            p0 = [_pt(ax, u - t["sup"] * (u - cc[i - 1]), v, -eb)] if i else \
                [_pt(ax, -ea, v, -eb - t["hook"]), _pt(ax, -ea, v, -eb)]
            p1 = [_pt(ax, u + t["sup"] * (cc[i + 1] - u), v, -eb)] if i < len(cc) - 1 else \
                [_pt(ax, ez, v, -eb), _pt(ax, ez, v, -eb - t["hook"])]
            bars.append(p0 + p1)
    return bars


def build_ground_beams():
    """ST03: every GB_LINES span as a clear span between joints, per run; joints J1 at every span end."""
    t = GBEAM
    runs, nodes = _gb_runs(), _gb_nodes()
    jb = {p: w for p, (_, _, w) in nodes.items()}
    assert all(abs(w - t["b"]) < 1e-9 for w in jb.values()), "joint width differs from the beam width"
    stubs = {g for gs in STUB_GRIDS.values() for g in gs}
    aw, zt, zb = t["b"] / 2 - t["cover"] - t["dt"] / 2, -t["cover"] - t["dt"] / 2, -t["h"] + t["cover"] + t["dt"] / 2
    k = t["shook"] / math.sqrt(2)
    c = _clear(C_GB)
    conc = mat("M_Concrete", (0.50, 0.50, 0.48), 0.85)
    lean_m = mat("M_LeanConcrete", (0.30, 0.30, 0.28), 0.95)
    sand_m = mat("M_Sand", (0.76, 0.68, 0.52), 0.95)
    steel = mat("M_Rebar", (0.28, 0.17, 0.11), 0.55, 0.6)
    axis = {r["name"]: r["ax"] for r in runs}
    lean, placed = {}, []
    for name, box in sorted(_gb_strips(runs, jb), key=lambda nb: axis[nb[0]]):   # along y gives way to along x
        pieces = [box]
        for p in placed:
            pieces = [q for r_ in pieces for q in _box_minus(r_, p)]
        placed += pieces
        lean.setdefault(name, []).extend(pieces)
    sand = lambda b: (*b[:2], GL, *b[3:5], b[2])                            # same footprint, GL → lean bottom

    def link(root_name, loc, props, parts):
        root = bpy.data.objects.new(root_name, None)
        root.empty_display_type, root.empty_display_size = "PLAIN_AXES", 0.2
        root.location = loc
        for kk, v in props.items():
            root[kk] = v
        c.objects.link(root)
        for kk, data in parts.items():
            ob = bpy.data.objects.new(f"{root_name}_{kk}", data)
            ob.parent = root
            c.objects.link(ob)

    for r in runs:
        name, ax, o, top = r["name"], r["ax"], r["o"], r["top"]
        loc = (o[0], o[1], top)
        rel = lambda b: tuple(b[i] - loc[i % 3] for i in range(6))
        cs = _clear_spans(r, jb)
        stirrups = []
        for s0, s1, _ in cs:
            L = s1 - s0
            assert L > 2 * t["first"], f"{name}: span too short for stirrups"
            n = math.ceil((L - 2 * t["first"]) / t["s"] - 1e-9) + 1
            for i in range(n):
                u = s0 + t["first"] + i * (L - 2 * t["first"]) / (n - 1)
                stirrups.append([_pt(ax, u, v, z) for v, z in
                                 ((aw - k, zt - k), (aw, zt), (-aw, zt), (-aw, zb), (aw, zb), (aw, zt), (aw - k, zt - k))])
        types = "/".join(sorted({tp for *_, tp in r["spans"]}))
        parts = {
            "Conc": _boxes_data(f"GB_{name}_Conc", [_uv(ax, s0, -t["b"] / 2, -t["h"], s1, t["b"] / 2, 0) for s0, s1, _ in cs],
                                conc, element="concrete", th=f"คอนกรีตคานคอดิน {t['b']:.2f}×{t['h']:.2f}", type="GB",
                                grade=t["grade"], beam_types=types),
            "Lean": _boxes_data(f"GB_{name}_Lean", [rel(b) for b in lean[name]], lean_m, element="lean_concrete",
                                th=f"คอนกรีตหยาบรองท้องคาน {t['lean'] * 100:.0f} ซม.", type="GB"),
            "Sand": _boxes_data(f"GB_{name}_Sand", [rel(sand(b)) for b in lean[name]], sand_m, element="sand",
                                th="ทรายหยาบบดอัดใต้คาน (ดินเดิม → ใต้คอนกรีตหยาบ)", type="GB"),
            "Bars": _rebar_data(f"GB_{name}_Bars", _beam_bars(r, jb), t["d"], steel, element="rebar",
                                th="เหล็กเสริมคานคอดิน", type="GB", bar=t["bar"], dia_mm=round(t["d"] * 1000)),
            "Stirrups": _rebar_data(f"GB_{name}_Stirrups", stirrups, t["dt"], steel, element="stirrups",
                                    th="เหล็กปลอกคานคอดิน", type="GB", bar=t["tie"], dia_mm=round(t["dt"] * 1000),
                                    spacing=t["s"]),
        }
        link(f"GB_{name}", loc, dict(line=name, type="GB", beam_types=types), parts)
    shared, sq = {}, _gb_squares(nodes)
    for p, (zb0, zt0, b) in sorted(nodes.items()):
        hj = zt0 - zb0
        key = f"J1_B{round(b * 100)}_H{round(hj * 100)}"
        if key not in shared:
            shared[key] = (round(hj, 6), _box_data(f"{key}_Conc", -b / 2, -b / 2, 0, b / 2, b / 2, hj, conc,
                                                   element="concrete", th="คอนกรีตข้อต่อคาน–เสา (เทพร้อมคาน)",
                                                   type="J1", grade=t["grade"]))
        assert shared[key][0] == round(hj, 6), f"{key}: same name, other height"
        x, y = _pxy(p)
        parts = {"Conc": shared[key][1]}
        if p not in stubs:   # a joint on beams only: lean and sand under it too
            rel = lambda q: tuple(q[i] - (x, y, zb0)[i % 3] for i in range(6))
            parts["Lean"] = _box_data(f"J1_{p}_Lean", *rel(sq[p]), lean_m, element="lean_concrete",
                                      th=f"คอนกรีตหยาบรองท้องคาน {t['lean'] * 100:.0f} ซม.", type="GB")
            parts["Sand"] = _box_data(f"J1_{p}_Sand", *rel(sand(sq[p])), sand_m, element="sand",
                                      th="ทรายหยาบบดอัดใต้คาน (ดินเดิม → ใต้คอนกรีตหยาบ)", type="GB")
        link(f"J1_{p}", (x, y, zb0), dict(grid=p, type="J1"), parts)
    bpy.context.view_layer.update()
    return len(runs), len(nodes)


# ---------------------------------------------------------------- ST03 selfcheck (model against the spec)

def _check_beams(rows_before):
    """rows_before: qto rows of the earlier stages (for the clash check). Every fault tagged [..]."""
    def eq(a, b, what):
        assert abs(a - b) <= 1e-5 * max(abs(b), 1e-9), f"[{what}] model {a:.6f} != expected {b:.6f}"
    t, r = GBEAM, qto(C_GB)
    runs, nodes = _gb_runs(), _gb_nodes()
    jb = {p: w for p, (_, _, w) in nodes.items()}
    stubs = {g for gs in STUB_GRIDS.values() for g in gs}
    h, b = t["h"], t["b"]
    g_ = lambda el, tp="GB": r.get((el, tp)) or dict(n=0, vol=0.0, side=0.0, bars=[], boxes=[])
    for el, n in (("concrete", len(runs)), ("rebar", len(runs)), ("stirrups", len(runs))):
        assert g_(el)["n"] == n, f"[count] beam {el}: {g_(el)['n']} objects, {n} runs"
    assert g_("concrete", "J1")["n"] == len(nodes), f"[count] joints: {g_('concrete', 'J1')['n']}, {len(nodes)} nodes"
    # hand formulas
    clear = sum(s1 - s0 for rr in runs for s0, s1, _ in _clear_spans(rr, jb))
    eq(clear, sum(abs(_pxy(a_)[0] - _pxy(b_)[0]) + abs(_pxy(a_)[1] - _pxy(b_)[1]) - b for a_, b_, *_ in GB_LINES),
       "beam concrete")   # clear spans = centre spans − one joint width each
    eq(g_("concrete")["vol"], clear * b * h, "beam concrete")
    eq(g_("concrete", "J1")["vol"], len(nodes) * b * b * h, "joint concrete")
    objs = {o.name: o for o in _coll(C_GB).objects}

    def boxes(name):
        bm = _world_bm(objs[name])
        try:
            return _obj_boxes(bm, name)
        finally:
            bm.free()
    eb = t["cover"] + t["dt"] + t["d"] / 2
    ea_ = b / 2 - eb
    exp_bars, nlap, exp_st = 0.0, 0, 0.0
    aw, hz = b / 2 - t["cover"] - t["dt"] / 2, h - 2 * t["cover"] - t["dt"]

    def one(rr):
        nonlocal exp_bars, nlap, exp_st
        name, ax, o, top, G = rr["name"], rr["ax"], rr["o"], rr["top"], rr["G"]
        assert f"GB_{name}" in objs, f"[count] run {name} missing"
        cs = _clear_spans(rr, jb)
        bx = sorted(boxes(f"GB_{name}_Conc"), key=lambda q: q[ax])
        assert len(bx) == len(cs), f"[count] {name}: {len(bx)} span boxes, {len(cs)} spans"
        for q, (s0, s1, _) in zip(bx, cs):
            assert abs(q[2] - (top - h)) < 1e-5 and abs(q[5] - top) < 1e-5, f"[level] {name}: beam z {q[2]:.3f}..{q[5]:.3f}"
            assert abs(q[ax] - (o[ax] + s0)) < 1e-5 and abs(q[ax + 3] - (o[ax] + s1)) < 1e-5 and \
                abs(q[1 - ax] - (o[1 - ax] - b / 2)) < 1e-5 and abs(q[4 - ax] - (o[1 - ax] + b / 2)) < 1e-5, \
                f"[position] {name}: span box off its line / joint faces"
        for q in boxes(f"GB_{name}_Lean"):
            assert abs(q[5] - (top - h)) < 1e-5 and abs(q[5] - q[2] - t["lean"]) < 1e-5, f"[lean] {name}: lean not under the beam"
        for q in boxes(f"GB_{name}_Sand"):
            assert abs(q[2] - GL) < 1e-5 and abs(q[5] - (top - h - t["lean"])) < 1e-5, f"[sand] {name}: sand not GL → lean"
        # bars: inside the cover, ≤ one stock bar, continuous corner bars cover the run with exact laps
        bars = _world_bars(objs[f"GB_{name}_Bars"])
        M = objs[f"GB_{name}"].matrix_world.inverted()
        loc_bars = [[M @ p for p in bb] for bb in bars]
        lim = b / 2 - t["cover"] - t["dt"] - t["d"] / 2
        for bb in loc_bars:
            L = sum((bb[i + 1] - bb[i]).length for i in range(len(bb) - 1))
            assert L <= STOCK + 1e-6, f"[laps] {name}: a {L:.2f} m bar"
            for p in bb:
                assert abs(p[1 - ax]) <= lim + 1e-5 and -h + eb - 1e-5 <= p.z <= -eb + 1e-5, \
                    f"[cover] {name}: bar at v {p[1 - ax]:.3f} z {p.z:.3f}"
        for z in (-eb, eb - h):
            for v in (-lim, lim):
                pcs = sorted((min(p[ax] for p in bb), max(p[ax] for p in bb)) for bb in loc_bars
                             if all(abs(p[1 - ax] - v) < 1e-5 for p in bb) and sum(abs(p.z - z) < 1e-5 for p in bb) >= 2)
                assert pcs, f"[cover] {name}: no corner bar tight at the {t['cover']} cover (v {v:.3f}, z {z:.3f})"
                assert abs(pcs[0][0] + ea_) < 1e-5 and abs(pcs[-1][1] - (G + ea_)) < 1e-5, \
                    f"[laps] {name}: corner bar does not run joint to joint"
                for (p0, p1), (q0, q1) in zip(pcs, pcs[1:]):
                    assert abs(p1 - q0 - t["lap"]) < 1e-5, f"[laps] {name}: lap {p1 - q0:.3f} != {t['lap']}"
                nlap += len(pcs) - 1
        cc = [u for u, _ in rr["nodes"]]
        e = 4 * (G + 2 * ea_ + 2 * t["hook"])
        for i, (u0, u1, tp) in enumerate(rr["spans"]):
            bt, L = BEAM_TYPES[tp], u1 - u0
            e += bt["extra"] * (L + 2 * ea_) + bt["nsp"] * t["mid"] * L
        for i, u in enumerate(cc):
            adj = [rr["spans"][j][2] for j in (i - 1, i) if 0 <= j < len(rr["spans"])]
            n = max(BEAM_TYPES[tp]["nsp"] for tp in adj)
            e += n * ((t["sup"] * (u - cc[i - 1]) if i else ea_ + t["hook"]) +
                      (t["sup"] * (cc[i + 1] - u) if i < len(cc) - 1 else ea_ + t["hook"]))
        exp_bars += e
        # stirrups per clear span, read back from the model
        st = [[M @ p for p in s] for s in _world_bars(objs[f"GB_{name}_Stirrups"])]
        us = sorted(s[0][ax] for s in st)
        seen = 0
        for s0, s1, _ in cs:
            zs = [u for u in us if s0 < u < s1]
            seen += len(zs)
            assert len(zs) > 1 and abs(zs[0] - s0 - t["first"]) < 1e-5 and abs(s1 - zs[-1] - t["first"]) < 1e-5 and \
                all(1e-6 < q - p <= t["s"] + 1e-6 for p, q in zip(zs, zs[1:])), f"[stirrups] {name}: spacing"
        assert seen == len(us), f"[stirrups] {name}: stirrup outside a clear span"
        pts = [p for s in st for p in s]
        assert abs(max(abs(p[1 - ax]) for p in pts) - aw) < 1e-5 and \
            abs(max(p.z for p in pts) - min(p.z for p in pts) - hz) < 1e-5, f"[cover] {name}: stirrup size"
        exp_st += len(us) * (2 * (2 * aw + hz) + 2 * t["shook"])
    _each(runs, one, "beam runs")
    eq(sum(g_("rebar")["bars"]), exp_bars + nlap * t["lap"], "rebar length")
    eq(sum(g_("stirrups")["bars"]), exp_st, "stirrup length")
    sb = {o.parent["grid"]: o for o in _coll(C_STUB).objects if o.name.endswith("_Conc") and o.parent}

    def joint(p):
        x, y = _pxy(p)
        assert f"J1_{p}" in objs, f"[count] joint {p} missing"
        j = boxes(f"J1_{p}_Conc")[0]
        assert max(abs(j[0] - (x - b / 2)), abs(j[3] - (x + b / 2)), abs(j[1] - (y - b / 2)), abs(j[4] - (y + b / 2))) < 1e-5, \
            f"[position] joint {p} off its point"
        assert abs(j[2] - (GB_TOP - h)) < 1e-5 and abs(j[5] - GB_TOP) < 1e-5, f"[level] joint {p} z {j[2]:.3f}..{j[5]:.3f}"
        if p in stubs:
            bm = _world_bm(sb[p])
            try:
                s = _obj_boxes(bm, "stub")[0]
            finally:
                bm.free()
            assert abs(s[5] - j[2]) < 1e-5 and all(abs(s[i] - j[i]) < 1e-5 for i in (0, 1, 3, 4)), f"[level] joint {p} not on its stub"
    _each(sorted(nodes), joint, "joints")
    # totals after the per-piece checks, so a moved piece reports where it is, not only a changed sum
    ends = {}
    for a_, b_, *_ in GB_LINES:
        for p in (a_, b_):
            ends[p] = ends.get(p, 0) + 1
    eq(g_("concrete")["side"], 2 * h * clear, "beam formwork")
    eq(g_("concrete", "J1")["side"], sum(4 * b * h - ends[p] * b * h for p in nodes), "joint formwork")
    strips, sq = [bx for _, bx in _gb_strips(runs, jb)], list(_gb_squares(nodes).values())
    eq(g_("lean_concrete")["vol"], _union_volume(strips + sq), "lean")
    eq(g_("sand")["vol"], _union_volume([(*q[:2], GL, *q[3:5], q[2]) for q in strips + sq]), "sand")
    solids = [bx for rows in (rows_before, r) for (el, _), x in rows.items() if el != "excavation" for bx in x["boxes"]]
    clash = [(a_, b_) for a_, b_ in itertools.combinations(solids, 2) if (i := _inter(a_, b_)) and _vol(i) > 1e-6]
    assert not clash, f"[clash] {len(clash)} solid pairs share volume (footings/stubs/beams)"
    return f"ST03 ok: {len(runs)} runs, {len(GB_LINES)} spans, {len(nodes)} joints, clear {clear:.2f} m, {nlap} laps"
