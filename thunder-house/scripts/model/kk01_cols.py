"""KK01 ST05 เสาชั้น 1 C1 – exec'd after kk01_floor.py (kk01_load.py). Cast before the floor topping (holes left in ST04).

C1 0.20 × 0.20 (S-03 พื้น–หลังคา) on the joint J1 top +0.70 up to the column top: +4.30 under the main roof's wall
plate (A-10 "ระดับหัวเสา"); rows A and B carry the lean-to's rafter support 2[]125×50 with its top at +3.30 (A-11) →
column top +3.175. Steel plate 160 × 160 × 6 on top (assumed, practice), its top at the column top. 4-DB12 from the
beam top +0.70 (lap 0.60 with the stub's corner starters, which stop at +1.30) to just under the plate, bent 90°
`bend` there like a pinwheel. Ties RB6 @0.15 from the stub top +0.30 through the beam joint up to the plate (practice),
first / last 5 cm from the ends, 135° hooks 75 mm, cover 0.03 to the tie (S-03).
Objects: C1_<grid> root at the joint top, children _Conc, _Plate, _Bars, _Ties. Spec: ST05_columns_spec.md.
"""

COL = dict(b=0.20, cover=0.03, d=0.012, n=4, bend=0.06, plate=0.16, pt=0.006, dt=0.006, s=0.15, first=0.05,
           hook=0.075, bottom=GB_TOP, tie_from=STUB_TOP, grade="St.240 ksc", bar="DB12 SD40", tie="RB6 SR24",
           plate_spec="PL 160×160×6 mm")
COL_TOP_MAIN = 4.30 - 0.125                      # A-10 "ระดับหัวเสา +4.30" = top of the wall plate 2[]125 (ST07: ridges
                                                 # +6.28 / +5.87 / +5.44 come out only so) → column top +4.175
COL_TOP_LEAN = 3.30 - 0.125                      # A-11 top of the rafter support 2[]125 at +3.30
LEAN_ROWS = ("A", "B")
C_COL = "KK01 ST05 Columns"
STAGES.insert(STAGES.index(C_FLOOR), C_COL)      # cast order: columns before the floor


def _col_top(g):
    return COL_TOP_LEAN if g[0] in LEAN_ROWS else COL_TOP_MAIN


def _col_bars(t, top_rel):
    """Bars and ties relative to the column root (joint top centre); top_rel = column top above the root."""
    a = t["b"] / 2 - t["cover"] - t["dt"] / 2
    m = a - t["dt"] / 2 - t["d"] / 2
    assert t["n"] == 4, "C1 has 4 corner bars"
    assert t["bend"] <= 2 * m - t["d"] + 1e-9, "top bends would hit the next corner bar"
    zt = top_rel - t["pt"] - t["d"] / 2                              # bar centre just under the plate
    bend = lambda sx, sy: (sx * (m - t["bend"]), sy * m, zt) if sx == sy else (sx * m, sy * (m - t["bend"]), zt)
    bars = [[(sx * m, sy * m, 0.0), (sx * m, sy * m, zt), bend(sx, sy)] for sx in (-1, 1) for sy in (-1, 1)]
    z0, z1 = t["tie_from"] - t["bottom"] + t["first"], top_rel - t["pt"] - t["first"]
    nt = math.ceil((z1 - z0) / t["s"] - 1e-9) + 1
    k = a - t["hook"] / math.sqrt(2)
    ties = [[(k, k, z), (a, a, z), (-a, a, z), (-a, -a, z), (a, -a, z), (a, a, z), (k, k, z)]
            for z in (z0 + i * (z1 - z0) / (nt - 1) for i in range(nt))]
    return bars, ties


def build_columns():
    """ST05: a C1 column on every stub's joint."""
    t = COL
    c = _clear(C_COL)
    conc = mat("M_Concrete", (0.50, 0.50, 0.48), 0.85)
    steel = mat("M_Rebar", (0.28, 0.17, 0.11), 0.55, 0.6)
    plate_m = mat("M_SteelPlate", (0.35, 0.37, 0.40), 0.4, 0.9)
    shared, n = {}, 0
    for gs in STUB_GRIDS.values():
        for g in gs:
            top = _col_top(g)
            h = top - t["bottom"]
            key = f"C1_H{round(h * 1000)}"
            if key not in shared:
                bars, ties = _col_bars(t, h)
                w, pw = t["b"] / 2, t["plate"] / 2
                shared[key] = (round(h, 6), {
                    "Conc": _box_data(f"{key}_Conc", -w, -w, 0, w, w, h - t["pt"], conc, element="concrete",
                                      th="คอนกรีตเสา C1", type="C1", grade=t["grade"]),
                    "Plate": _box_data(f"{key}_Plate", -pw, -pw, h - t["pt"], pw, pw, h, plate_m, element="plate",
                                       th=f"แผ่นเหล็กหัวเสา {t['plate_spec']}", type="C1"),
                    "Bars": _rebar_data(f"{key}_Bars", bars, t["d"], steel, element="rebar", th="เหล็กเสริมเสา (ทาบเหล็กยืนตอม่อ)",
                                        type="C1", bar=t["bar"], dia_mm=round(t["d"] * 1000)),
                    "Ties": _rebar_data(f"{key}_Ties", ties, t["dt"], steel, element="ties",
                                        th="เหล็กปลอกเสา (จากยอดตอม่อผ่านข้อต่อคานถึงหัวเสา)", type="C1", bar=t["tie"],
                                        dia_mm=round(t["dt"] * 1000), spacing=t["s"]),
                })
            assert shared[key][0] == round(h, 6), f"{key}: same name, other height"
            x, y = _pxy(g)
            root = bpy.data.objects.new(f"C1_{g}", None)
            root.empty_display_type, root.empty_display_size = "PLAIN_AXES", 0.2
            root.location = (x, y, t["bottom"])
            root["grid"], root["type"] = g, "C1"
            c.objects.link(root)
            for k_, data in shared[key][1].items():
                o = bpy.data.objects.new(f"C1_{g}_{k_}", data)
                o.parent = root
                c.objects.link(o)
            n += 1
    bpy.context.view_layer.update()
    return n


def _check_columns(rows_before):
    def eq(a, b, what):
        assert abs(a - b) <= 1e-5 * max(abs(b), 1e-9), f"[{what}] model {a:.6f} != expected {b:.6f}"
    t, r = COL, qto(C_COL)
    gs = [g for v in STUB_GRIDS.values() for g in v]
    g_ = lambda el: r.get((el, "C1")) or dict(n=0, vol=0.0, side=0.0, bars=[], boxes=[])
    for el in ("concrete", "plate", "rebar", "ties"):
        assert g_(el)["n"] == len(gs), f"[count] column {el}: {g_(el)['n']} objects, {len(gs)} columns"
    H = sum(_col_top(g) - t["pt"] - t["bottom"] for g in gs)
    eq(g_("concrete")["vol"], t["b"] ** 2 * H, "column concrete")
    pv = len(gs) * t["plate"] ** 2 * t["pt"]   # 6 mm at z ≈ 4 m: float32 gives ~1e-4 of it — looser tolerance
    assert abs(g_("plate")["vol"] - pv) <= 2e-3 * pv, f"[plate] model {g_('plate')['vol']:.6f} != expected {pv:.6f}"
    a = t["b"] / 2 - t["cover"] - t["dt"] / 2
    m = a - t["dt"] / 2 - t["d"] / 2
    objs = {o.name: o for o in _coll(C_COL).objects}
    sobj = {o.name: o for o in _coll(C_STUB).objects}
    joints = {o.parent["grid"]: o for o in _coll(C_GB).objects if o.name.startswith("J1_") and o.name.endswith("_Conc")}
    exp_bars, exp_ties = [0.0], [0.0]

    def box(o):
        bm = _world_bm(o)
        try:
            return _obj_boxes(bm, o.name)[0]
        finally:
            bm.free()

    def one(g):
        x, y = _pxy(g)
        assert f"C1_{g}" in objs, f"[count] column {g} missing"
        top = _col_top(g)
        cb, pl, jb_ = box(objs[f"C1_{g}_Conc"]), box(objs[f"C1_{g}_Plate"]), box(joints[g])
        w = t["b"] / 2
        assert max(abs(cb[0] - (x - w)), abs(cb[3] - (x + w)), abs(cb[1] - (y - w)), abs(cb[4] - (y + w))) < 1e-5, \
            f"[position] column {g} off its grid point"
        assert abs(cb[2] - jb_[5]) < 1e-5 and abs(cb[2] - GB_TOP) < 1e-5, f"[level] column {g} not on its joint (z {cb[2]:.3f})"
        assert abs(pl[5] - top) < 1e-5 and abs(pl[2] - cb[5]) < 1e-5 and abs(pl[5] - pl[2] - t["pt"]) < 2e-5, \
            f"[plate] column {g}: plate z {pl[2]:.3f}..{pl[5]:.3f}, column top {top}"
        assert abs(pl[3] - pl[0] - t["plate"]) < 1e-5 and abs((pl[0] + pl[3]) / 2 - x) < 1e-5 and abs((pl[1] + pl[4]) / 2 - y) < 1e-5, \
            f"[plate] column {g}: plate size / centre"
        bars = _world_bars(objs[f"C1_{g}_Bars"])
        assert len(bars) == t["n"], f"[bars] column {g}: {len(bars)} bars, S-03 has {t['n']}"
        starters = _world_bars(sobj[f"P1_{g}_Bars"])
        zt = top - t["pt"] - t["d"] / 2
        for b in bars:
            assert abs(abs(b[0].x - x) - m) < 1e-5 and abs(abs(b[0].y - y) - m) < 1e-5, f"[cover] column {g}: bar not at the corner"
            assert abs(b[1].z - zt) < 1e-5, f"[bars] column {g}: bar top {b[1].z:.3f} != under the plate {zt:.3f}"
            assert abs((b[2] - b[1]).length - t["bend"]) < 1e-5, f"[bars] column {g}: bend {(b[2] - b[1]).length:.3f}"
            st = [s for s in starters if abs(s[-1].x - b[0].x) < 1e-5 and abs(s[-1].y - b[0].y) < 1e-5]
            assert st, f"[lap] column {g}: no stub starter under the bar"
            lap = st[0][-1].z - b[0].z
            assert abs(b[0].z - GB_TOP) < 1e-5 and abs(lap - STUBS["P1"]["lap"]) < 1e-5, \
                f"[lap] column {g}: bar from {b[0].z:.3f}, lap with the starter {lap:.3f}"
            exp_bars[0] += (zt - GB_TOP) + t["bend"]
        # pinwheel: four bends point four different ways
        dirs = {(round((b[2] - b[1]).x, 3), round((b[2] - b[1]).y, 3)) for b in bars}
        assert len(dirs) == 4, f"[bars] column {g}: top bends not a pinwheel"
        ties = _world_bars(objs[f"C1_{g}_Ties"])
        zs = sorted(tb[0].z for tb in ties)
        z0, z1 = t["tie_from"] + t["first"], top - t["pt"] - t["first"]
        assert abs(zs[0] - z0) < 1e-5 and abs(zs[-1] - z1) < 1e-5, f"[ties] column {g}: ties {zs[0]:.3f}..{zs[-1]:.3f}, spec {z0:.3f}..{z1:.3f}"
        gaps = [q - p for p, q in zip(zs, zs[1:])]
        assert max(gaps) <= t["s"] + 1e-5 and min(gaps) > 1e-4, f"[ties] column {g}: gaps {min(gaps):.3f}..{max(gaps):.3f}"
        for tb in ties:
            hx = max(abs(p.x - x) for p in tb)
            assert abs(hx - a) < 1e-5, f"[cover] column {g}: tie half-size {hx:.4f} != {a:.4f}"
        exp_ties[0] += len(ties) * (8 * a + 2 * t["hook"])
    _each(gs, one, "columns")
    eq(sum(g_("rebar")["bars"]), exp_bars[0], "rebar length")
    eq(sum(g_("ties")["bars"]), exp_ties[0], "tie length")
    eq(g_("concrete")["side"], 4 * t["b"] * H, "column formwork")
    solids = [bx for rows in (rows_before, r) for (el, _), x in rows.items() if el != "excavation" for bx in x["boxes"]]
    clash = [(a_, b_) for a_, b_ in itertools.combinations(solids, 2) if (i := _inter(a_, b_)) and _vol(i) > 1e-7]
    assert not clash, f"[clash] {len(clash)} solid pairs share volume (columns vs the rest)"
    nl = sum(g[0] in LEAN_ROWS for g in gs)
    return f"ST05 ok: {len(gs)} columns ({len(gs) - nl} to +{COL_TOP_MAIN:.2f}, {nl} to +{COL_TOP_LEAN:.3f}), " \
           f"{len(ties_of(objs, gs[0]))}+ ties each"


def ties_of(objs, g):
    return _world_bars(objs[f"C1_{g}_Ties"])
