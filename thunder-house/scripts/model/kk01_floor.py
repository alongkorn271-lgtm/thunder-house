"""KK01 ST04 พื้นชั้น 1 – exec'd after kk01_beams.py (kk01_load.py).

S-02 panels (FLOOR_PANELS, beam-centre corners) and A-04 levels (finished floors: the structure stops FINISH lower):
  PS  แผ่นพื้นสำเร็จ 0.35 × 0.05 on the beam tops (+0.67), across the short direction of the panel, bearing `bear` each
      end; planks side by side from one beam face, the strip left over (< 0.35) is cast with the topping on a form.
      Topping to FL2 − 0.03 = +0.77 over the PS panels and every beam / joint round them (0.05 on planks, 0.10 on
      beams), kept off the wet side of a wall on a PS–S beam (`_wet_cuts`: no topping ledge in a bath), wire
      mesh 4 mm @0.10 (S-03 PS: "RB6 @0.20 or wire mesh 4 mm @0.10"), RB6 @0.30 hook bars over the plank supports
      (S-03: 0.60 over an inner beam, 0.30 at an edge). Left open at the 23 columns (cast before the floor, practice).
  S   พื้นหล่อในที่ 0.125, top +0.67 (bath / verandah / laundry, FL3/FL4 +0.70), between the beam faces: RB9 @0.15 short /
      @0.30 long at the bottom, 0.10 into the beams; top RB9 @0.30 over every edge L/4 (L = short clear span) — S-03.
Objects: PS_<a>-<b> (_Planks, _Hooks), S_<a>-<b> (_Conc, _Bars), TOP_FL2 (_Conc, _Mesh). Spec: ST04_floor_spec.md.
"""

FL2 = 0.80                    # A-04 finished floors (user, ST11: +0.80 is the tile face)
FL_WET = 0.70                 # FL3 / FL4 verandah, laundry, baths
FINISH = 0.03                 # screed + adhesive + tile (practice: tiles 3 cm go with the finishes)
FLOOR_PANELS = [   # (corner, opposite corner, kind) — S-02 circles; Ga3–G5 front verandah has none: S like FL3 (assumed).
    # D5–F5a: PS on S-02, but it lies inside bath 2 (A-04: FL4 +0.70 for the whole room, door D4 over x 10.5) → S (ST11)
    ("A2", "B4", "PS"), ("A4", "B5", "PS"), ("C1", "E3", "PS"), ("C3", "E5", "PS"), ("C5", "D6", "PS"),
    ("E1a", "Gb2", "PS"), ("Gb1", "G2", "PS"), ("E2", "G3", "PS"), ("E3", "Ga5", "PS"), ("D5", "F5a", "S"),
    ("F5", "G6", "PS"),
    ("B2", "C4", "S"), ("B4", "C5", "S"), ("B5", "C6", "S"), ("A5", "B5a", "S"), ("E1", "Gb1a", "S"),
    ("D5a", "F6", "S"), ("Ga3", "G5", "S")]
PS = dict(w=0.35, t=0.05, bear=0.07, ll="LL ≥ 250 kg/m² (S-03)")
TOPPING = dict(top=FL2 - FINISH, mesh_d=0.004, mesh_s=0.10, mesh_cover=0.03, mesh_z=FL2 - FINISH - 0.025, hook_d=0.006, hook_s=0.30,
               hook_in=0.60, hook_edge=0.30, hook_cover=0.03, first=0.05, holes=True, grade="St.240 ksc",
               mesh="Wire mesh 4 mm @0.10", hook_bar="RB6 SR24")
assert abs(GB_TOP + FINISH - FL_WET) < 1e-9 and abs(GB_TOP + PS["t"] + 0.05 + FINISH - FL2) < 1e-9, "floor levels"
SSLAB = dict(t=0.125, top=GB_TOP, d=0.009, s_short=0.15, s_long=0.30, s_top=0.30, top_frac=0.25, anchor=0.10,
             cover=0.02, first=0.05, grade="St.240 ksc", bar="RB9 SR24")
C_FLOOR = "KK01 ST04 Floor"
STAGES.append(C_FLOOR)


def _prect(a, b):
    (xa, ya), (xb, yb) = _pxy(a), _pxy(b)
    return min(xa, xb), min(ya, yb), max(xa, xb), max(ya, yb)


def _inset(r, w=None):
    w = GBEAM["b"] / 2 if w is None else w
    return r[0] + w, r[1] + w, r[2] - w, r[3] - w


def _edge_on_beams(ax, k, lo, hi):
    """The segment along axis ax (0 = x) at the other coordinate k, lo..hi, lies on GB_LINES spans."""
    iv = []
    for a, b, *_ in GB_LINES:
        pa, pb = _pxy(a), _pxy(b)
        if abs(pa[1 - ax] - k) < 1e-9 and abs(pb[1 - ax] - k) < 1e-9 and pa[ax] != pb[ax]:
            iv.append(tuple(sorted((pa[ax], pb[ax]))))
    u = lo
    for a, b in sorted(iv):
        if a <= u + 1e-9:
            u = max(u, b)
    return u >= hi - 1e-9


def _panels():
    """[(name, kind, rect)] with every edge on beams; no two panels overlap."""
    out = []
    for a, b, kind in FLOOR_PANELS:
        assert kind in ("PS", "S"), f"panel {a}-{b}: kind {kind}"
        r = _prect(a, b)
        for ax, k, lo, hi in ((0, r[1], r[0], r[2]), (0, r[3], r[0], r[2]), (1, r[0], r[1], r[3]), (1, r[2], r[1], r[3])):
            assert _edge_on_beams(ax, k, lo, hi), f"[beams] panel {a}-{b}: edge {'xy'[ax]} at {k} not on a beam"
        out.append((f"{a}-{b}", kind, r))
    for (n1, _, r1), (n2, _, r2) in itertools.combinations(out, 2):
        assert min(r1[2], r2[2]) - max(r1[0], r2[0]) < 1e-9 or min(r1[3], r2[3]) - max(r1[1], r2[1]) < 1e-9, \
            f"panels {n1} and {n2} overlap"
    return out


def _ps_layout(r):
    """(span axis, planks [(x0, y0, x1, y1)], fill strip rect or None) of a PS panel; span = short clear direction
    (equal: along x, as S-02 draws the arrows)."""
    c = _inset(r)
    L = (c[2] - c[0], c[3] - c[1])
    sa = 0 if L[0] <= L[1] + 1e-9 else 1
    n = int(math.floor(L[1 - sa] / PS["w"] + 1e-9))
    planks = []
    for i in range(n):
        v0 = c[1 - sa] + i * PS["w"]
        u0, u1 = c[sa] - PS["bear"], c[sa + 2] + PS["bear"]
        planks.append((u0, v0, u1, v0 + PS["w"]) if sa == 0 else (v0, u0, v0 + PS["w"], u1))
    v = c[1 - sa] + n * PS["w"]
    fill = None if c[3 - sa] - v < 1e-6 else ((c[0], v, c[2], c[3]) if sa == 0 else (v, c[1], c[2], c[3]))
    return sa, planks, fill


def _cut(box, cutters):
    pieces = [box]
    for c in cutters:
        pieces = [q for p in pieces for q in _box_minus(p, c)]
    return pieces


def _disjoint(boxes):
    """Union of boxes as disjoint boxes (each new box minus everything placed)."""
    out = []
    for b in boxes:
        out += _cut(b, out)
    return out


def _col_squares():
    """Column footprints (0.20 at every stub point) through the topping layer: kept open for the columns."""
    w = GBEAM["b"] / 2
    return [(x - w, y - w, GB_TOP, x + w, y + w, TOPPING["top"]) for gs in STUB_GRIDS.values() for g in gs
            for x, y in (_pxy(g),)]


def _wet_cuts():
    """Boxes (GB_TOP → topping top) the topping keeps off: on a beam between a PS and an S panel carrying a wall, from
    the S panel's beam face back to the wall's brick face on the S side (else a 5 cm topping ledge 0.10 high runs along
    the bath / verandah wall, under its finish). Zero-width strips (flush walls on the S face) are dropped."""
    w, t, out = GBEAM["b"] / 2, BRICK["t"], []
    lines = [_wl(x) for x in WALLS]
    for _, kind, r in _panels():
        if kind != "S":
            continue
        for ax, k, sgn in ((0, r[1], 1), (0, r[3], -1), (1, r[0], 1), (1, r[2], -1)):   # edge along ax, S side +sgn
            lo, hi = r[ax] - w, r[ax + 2] + w          # to the beam's outer face, or to the S face of a wall across it
            for _, lax, kc, u0, u1, *_ in lines:
                if lax != ax and u0 - 1e-9 <= k <= u1 + 1e-9:
                    if abs(kc - r[ax]) < w - 1e-9:
                        lo = max(lo, kc + t / 2)
                    if abs(kc - r[ax + 2]) < w - 1e-9:
                        hi = min(hi, kc - t / 2)
            for _, lax, kc, u0, u1, *_ in lines:
                if lax != ax or abs(kc - k) > w - 1e-9:
                    continue
                f, b = kc + sgn * t / 2, k + sgn * w
                a0, a1 = max(lo, u0 - w), min(hi, u1 + w)
                if a1 - a0 < 1e-6 or (b - f) * sgn < 1e-6:
                    continue
                v0, v1 = sorted((f, b))
                out.append((a0, v0, GB_TOP, a1, v1, TOPPING["top"]) if ax == 0 else (v0, a0, GB_TOP, v1, a1, TOPPING["top"]))
    return out


def _footprint():
    """Topping footprint 2D (z 0..1 dummy) as disjoint boxes: PS panels grown to the beams' outer faces, minus columns,
    minus the wet cuts."""
    w = GBEAM["b"] / 2
    fp = _disjoint([(r[0] - w, r[1] - w, 0.0, r[2] + w, r[3] + w, 1.0) for _, k, r in _panels() if k == "PS"])
    if TOPPING["holes"]:
        fp = [q for b in fp for q in _cut(b, [(c[0], c[1], 0.0, c[3], c[4], 1.0) for c in _col_squares()])]
    fp = [q for b in fp for q in _cut(b, [(c[0], c[1], 0.0, c[3], c[4], 1.0) for c in _wet_cuts()])]
    return [q for q in fp if q[3] - q[0] > 1e-6 and q[4] - q[1] > 1e-6]


def _erode(boxes, c):
    """2D boxes eroded by c: the bounding box minus the outside grown by c."""
    x0, y0 = min(b[0] for b in boxes) - 1, min(b[1] for b in boxes) - 1
    x1, y1 = max(b[3] for b in boxes) + 1, max(b[4] for b in boxes) + 1
    outside = _cut((x0, y0, 0.0, x1, y1, 1.0), boxes)
    grown = [(b[0] - c, b[1] - c, 0.0, b[3] + c, b[4] + c, 1.0) for b in outside]
    return [q for q in _cut((x0 + c, y0 + c, 0.0, x1 - c, y1 - c, 1.0), grown) if q[3] - q[0] > 1e-6 and q[4] - q[1] > 1e-6]


def _mesh_wires(boxes, s, z):
    """Wires on a global grid (origin at the lowest corner) clipped to 2D boxes; collinear pieces merged."""
    gx, gy = min(b[0] for b in boxes), min(b[1] for b in boxes)
    wires = []
    for ax in (0, 1):   # ax 0: wires along x at fixed y
        g0 = (gy, gx)[ax]
        lines = {}
        for b in boxes:
            lo, hi = b[1 - ax], b[4 - ax]
            k0 = math.ceil((lo - g0) / s - 1e-9)
            k = k0
            while g0 + k * s <= hi + 1e-9:
                lines.setdefault(k, []).append((b[ax], b[ax + 3]))
                k += 1
        for k, iv in lines.items():
            v = g0 + k * s
            iv.sort()
            merged = [list(iv[0])]
            for a, b in iv[1:]:
                if a <= merged[-1][1] + 1e-9:
                    merged[-1][1] = max(merged[-1][1], b)
                else:
                    merged.append([a, b])
            for a, b in merged:
                if b - a > 1e-6:
                    wires.append([(a, v, z), (b, v, z)] if ax == 0 else [(v, a, z), (v, b, z)])
    return wires


def _positions(lo, hi, s, first):
    n = math.ceil((hi - lo - 2 * first) / s - 1e-9) + 1
    return [lo + first + i * (hi - lo - 2 * first) / (n - 1) for i in range(n)]


def _hook_bars(panels):
    """RB6 hook bars over the PS bearing beams: [(points)] world. Inner beam (PS bearing on both sides): one bar
    `hook_in` centred on it, made by the lower panel; edge beam: `hook_edge` from the beam's outer face − cover."""
    t, w = TOPPING, GBEAM["b"] / 2
    ps = {n: (r, _ps_layout(r)) for n, k, r in panels if k == "PS"}
    z = t["mesh_z"] - t["mesh_d"] / 2 - t["hook_d"] / 2
    out, cuts = [], _wet_cuts()
    for n, (r, (sa, planks, _)) in ps.items():
        c = _inset(r)
        for side in (0, 1):
            u = r[sa + 2 * side]                                 # beam centre
            probe = u + (1 if side else -1) * (w + 0.05)
            other = [m for m, (r2, (sa2, _, _)) in ps.items() if m != n and sa2 == sa and
                     r2[sa] - 1e-9 <= probe <= r2[sa + 2] + 1e-9 and
                     min(r2[3 - sa], r[3 - sa]) - max(r2[1 - sa], r[1 - sa]) > 1e-6]
            if other and side == 0:
                continue                                         # the panel on the other side makes it
            vs = _positions(c[1 - sa], c[3 - sa], t["hook_s"], t["first"])
            if other:
                u0, u1 = u - t["hook_in"] / 2, u + t["hook_in"] / 2
            else:
                outer = u + (w if side else -w) - (t["hook_cover"] if side else -t["hook_cover"])
                u0, u1 = sorted((outer, outer + (-1 if side else 1) * t["hook_edge"]))
            for v in vs:
                a, b = u0, u1
                for c in cuts:                                   # an edge hook ends `hook_cover` short of a wet cut
                    if c[1 - sa] - 1e-9 <= v <= c[4 - sa] + 1e-9 and c[sa] < b and c[sa + 3] > a:
                        a, b = (max(a, c[sa + 3] + t["hook_cover"]), b) if c[sa] <= a + 1e-9 else                                (a, min(b, c[sa] - t["hook_cover"]))
                out.append([(a, v, z), (b, v, z)] if sa == 0 else [(v, a, z), (v, b, z)])
    return out


def _s_bars(r):
    """S slab bars (world) of panel rect r."""
    t = SSLAB
    c = _inset(r)
    L = (c[2] - c[0], c[3] - c[1])
    sa = 0 if L[0] <= L[1] + 1e-9 else 1                        # short direction
    zb = t["top"] - t["t"] + t["cover"] + t["d"] / 2
    zt = t["top"] - t["cover"] - t["d"] / 2
    bars = []
    for ax, s, z in ((sa, t["s_short"], zb), (1 - sa, t["s_long"], zb + t["d"])):   # bars running along ax
        for v in _positions(c[1 - ax], c[3 - ax], s, t["first"]):
            u0, u1 = c[ax] - t["anchor"], c[ax + 2] + t["anchor"]
            bars.append([(u0, v, z), (u1, v, z)] if ax == 0 else [(v, u0, z), (v, u1, z)])
    ext = t["top_frac"] * L[sa]
    for ax in (0, 1):                                            # top bars run along ax, over the two edges across it
        for side in (0, 1):
            f = c[ax + 2 * side]
            u0, u1 = (f - t["anchor"], f + ext) if side == 0 else (f - ext, f + t["anchor"])
            for v in _positions(c[1 - ax], c[3 - ax], t["s_top"], t["first"]):
                bars.append([(u0, v, zt), (u1, v, zt)] if ax == 0 else [(v, u0, zt), (v, u1, zt)])
    return sa, bars


def build_floor():
    """ST04: PS planks + topping + mesh + hook bars, S slabs, all from FLOOR_PANELS."""
    panels = _panels()
    c = _clear(C_FLOOR)
    conc = mat("M_Concrete", (0.50, 0.50, 0.48), 0.85)
    plank_m = mat("M_PrecastPlank", (0.62, 0.62, 0.60), 0.8)
    steel = mat("M_Rebar", (0.28, 0.17, 0.11), 0.55, 0.6)
    t, p = TOPPING, PS

    def link(name, loc, parts, **props):
        root = bpy.data.objects.new(name, None)
        root.empty_display_type, root.empty_display_size = "PLAIN_AXES", 0.2
        root.location = loc
        for k, v in props.items():
            root[k] = v
        c.objects.link(root)
        for k, data in parts.items():
            ob = bpy.data.objects.new(f"{name}_{k}", data)
            ob.parent = root
            c.objects.link(ob)

    rel = lambda b, o: tuple(b[i] - o[i % 3] for i in range(6))
    relp = lambda pts, o: [tuple(q[i] - o[i] for i in range(3)) for q in pts]
    all_planks, hooks = [], _hook_bars(panels)
    for name, kind, r in panels:
        o = (r[0], r[1], GB_TOP)
        if kind == "PS":
            sa, planks, _ = _ps_layout(r)
            notch = _col_squares() if t["holes"] else []          # planks notched round the columns cast before them
            boxes = [b for q in planks for b in _cut((q[0], q[1], GB_TOP, q[2], q[3], GB_TOP + p["t"]), notch)]
            all_planks += boxes
            parts = {"Planks": _boxes_data(f"PS_{name}_Planks", [rel(b, o) for b in boxes], plank_m, element="precast",
                                           th=f"แผ่นพื้นสำเร็จรูป PS {p['w']:.2f}×{p['t']:.2f} {p['ll']}", type="PS",
                                           span_axis="xy"[sa])}
            link(f"PS_{name}", o, parts, panel=name, type="PS")
        else:
            cl = _inset(r)
            sa, bars = _s_bars(r)
            parts = {"Conc": _box_data(f"S_{name}_Conc", *rel((cl[0], cl[1], SSLAB["top"] - SSLAB["t"], cl[2], cl[3], SSLAB["top"]), o),
                                       conc, element="concrete", th=f"พื้นหล่อในที่ S หนา {SSLAB['t']:.3f} (+{SSLAB['top']:.2f})",
                                       type="S", grade=SSLAB["grade"]),
                     "Bars": _rebar_data(f"S_{name}_Bars", [relp(b, o) for b in bars], SSLAB["d"], steel, element="rebar",
                                         th="เหล็กเสริมพื้น S", type="S", bar=SSLAB["bar"], dia_mm=round(SSLAB["d"] * 1000))}
            link(f"S_{name}", o, parts, panel=name, type="S", short_axis="xy"[sa])
    # topping: footprint × (beam top → FL2) minus planks and column holes
    fp = _footprint()
    holes = _col_squares() if t["holes"] else []
    top_boxes = [q for b in fp for q in _cut((b[0], b[1], GB_TOP, b[3], b[4], t["top"]), all_planks + holes)]
    o = (0.0, 0.0, 0.0)
    wires = _mesh_wires(_erode(fp, t["mesh_cover"]), t["mesh_s"], t["mesh_z"])
    link("TOP_FL2", o, {
        "Conc": _boxes_data("TOP_FL2_Conc", top_boxes, conc, element="concrete", type="TOP", grade=t["grade"],
                            th=f"คอนกรีตทับหน้า (topping) ถึง FL2 +{t['top']:.2f}"),
        "Mesh": _rebar_data("TOP_FL2_Mesh", wires, t["mesh_d"], steel, element="mesh", th="ตะแกรงเหล็ก wire mesh",
                            type="TOP", bar=t["mesh"], dia_mm=round(t["mesh_d"] * 1000), spacing=t["mesh_s"]),
        "Hooks": _rebar_data("TOP_FL2_Hooks", hooks, t["hook_d"], steel, element="rebar", th="เหล็กหนวดกุ้งเหนือคานรับ PS",
                             type="TOP", bar=t["hook_bar"], dia_mm=round(t["hook_d"] * 1000), spacing=t["hook_s"]),
    }, type="TOP")
    bpy.context.view_layer.update()
    return len(panels)



def floor_report():
    """Lines for the BOQ: planks by length, concrete, formwork (topping edges, fill-strip and S soffits), steel."""
    panels = _panels()
    against = [b for (el, _), x in qto(C_GB).items() if el == "concrete" for b in x["boxes"]] + _col_squares()
    r, out = qto(C_FLOOR, against), []
    pl = {}
    for name, kind, rc in panels:
        if kind == "PS":
            sa, planks, fill = _ps_layout(rc)
            for q in planks:
                L = round(q[sa + 2] - q[sa], 3)
                pl[L] = pl.get(L, 0) + 1
    area = sum(k * L * PS["w"] for L, k in pl.items())
    out.append(f"PS แผ่นพื้นสำเร็จ {PS['w']:.2f}×{PS['t']:.2f} {PS['ll']}: " +
               " · ".join(f"{k} แผ่น × {L:.2f} ม." for L, k in sorted(pl.items())) +
               f" = {sum(pl.values())} แผ่น {area:.2f} ตร.ม.")
    fills = sum((f[2] - f[0]) * (f[3] - f[1]) for _, k, rc in panels if k == "PS" for f in (_ps_layout(rc)[2],) if f)
    s_soffit = sum((c_[2] - c_[0]) * (c_[3] - c_[1]) for _, k, rc in panels if k == "S" for c_ in (_inset(rc),))
    for key, lab in ((("concrete", "TOP"), "topping"), (("concrete", "S"), "S")):
        x = r[key]
        out.append(f"{x['th']}: {x['vol']:.3f} ลบ.ม. · ไม้แบบข้าง {max(x['side'], 0.0):.2f} ตร.ม.")
    out.append(f"ไม้แบบท้องพื้น: S {s_soffit:.2f} ตร.ม. + ช่องเติมข้าง PS {fills:.2f} ตร.ม. = {s_soffit + fills:.2f} ตร.ม.")
    for key in (("mesh", "TOP"), ("rebar", "TOP"), ("rebar", "S")):
        x = r[key]
        m = sum(x["bars"])
        line = f"{x['th']} {x['bar']}: {len(x['bars'])} ท่อน = {m:.2f} ม. = {m * KG_M[x['dia']]:.1f} กก."
        if key[0] == "mesh":
            line += f" (พื้นที่ตะแกรง ≈ {m * TOPPING['mesh_s'] / 2:.2f} ตร.ม. ก่อนเผื่อทาบ)"
        else:
            line += f" → ใช้เหล็กเส้น 10 ม. {_stock_bars(x['bars'])} เส้น"
        out.append(line)
    poured = r[("concrete", "TOP")]["vol"] + r[("concrete", "S")]["vol"]
    out.append(f"คอนกรีตเทครั้งนี้ {poured:.3f} ลบ.ม. → สั่ง {math.ceil(poured * 2 - 1e-9) / 2:.1f} ลบ.ม.")
    return "\n".join(out)


# ---------------------------------------------------------------- ST04 selfcheck

def _check_floor(rows_before):
    def eq(a, b, what):
        assert abs(a - b) <= 1e-5 * max(abs(b), 1e-9), f"[{what}] model {a:.6f} != expected {b:.6f}"
    panels = _panels()
    r = qto(C_FLOOR)
    objs = {o.name: o for o in _coll(C_FLOOR).objects}
    t, p, s_ = TOPPING, PS, SSLAB
    nps = sum(k == "PS" for _, k, _ in panels)
    ns = len(panels) - nps
    g_ = lambda el, tp: r.get((el, tp)) or dict(n=0, vol=0.0, side=0.0, bars=[], boxes=[])
    assert g_("precast", "PS")["n"] == nps and g_("concrete", "S")["n"] == ns, \
        f"[count] {g_('precast', 'PS')['n']} PS / {g_('concrete', 'S')['n']} S panels, S-02 has {nps} / {ns}"
    beam_tops = [b for (el, _), x in qto(C_GB).items() if el == "concrete" for b in x["boxes"]]

    def boxes(name):
        bm = _world_bm(objs[name])
        try:
            return _obj_boxes(bm, name)
        finally:
            bm.free()
    plank_vol = [0.0]

    def panel(item):
        name, kind, rc = item
        cl = _inset(rc)
        if kind == "PS":
            assert f"PS_{name}" in objs, f"[count] PS {name} missing"
            bx = boxes(f"PS_{name}_Planks")
            Lc = (cl[2] - cl[0], cl[3] - cl[1])
            sa = 0 if Lc[0] <= Lc[1] + 1e-9 else 1               # short clear direction, read from the spec here
            n = int(math.floor(Lc[1 - sa] / p["w"] + 1e-9))
            notch = _col_squares() if t["holes"] else []
            env = [None] * 6                                    # n planks side by side from the beam face, full length
            env[sa], env[sa + 3] = cl[sa] - p["bear"], cl[sa + 2] + p["bear"]
            env[1 - sa], env[4 - sa] = cl[1 - sa], cl[1 - sa] + n * p["w"]
            env[2], env[5] = GB_TOP, GB_TOP + p["t"]
            env = tuple(env)
            for q in bx:
                assert abs(q[2] - GB_TOP) < 1e-5 and abs(q[5] - GB_TOP - p["t"]) < 1e-5, f"[level] PS {name}: plank z {q[2]:.3f}"
                assert all(q[i] >= env[i] - 1e-5 and q[i + 3] <= env[i + 3] + 1e-5 for i in (0, 1)),                     f"[planks] PS {name}: plank outside {n} × {p['w']} across, clear {Lc[sa]:.2f} + 2 × {p['bear']}"
            full = _vol(env) - sum(_vol(i) for h in notch if (i := _inter(env, h)))
            eq(sum(_vol(q) for q in bx), full, "planks")
            for lo, hi in ((env[sa], cl[sa]), (cl[sa + 2], env[sa + 3])):   # bearing strips rest on beams / joints
                strip = list(env)
                strip[sa], strip[sa + 3] = lo, hi
                strip[2], strip[5] = GB_TOP - 0.01, GB_TOP
                strip = tuple(strip)
                pieces = _cut(strip, [(h[0], h[1], strip[2], h[3], h[4], strip[5]) for h in notch])
                on = sum(_vol(i) for pc in pieces for bb in beam_tops if (i := _inter(pc, bb)))
                st_top = (*strip[:2], GB_TOP, *strip[3:5], GB_TOP + p["t"])
                laid = sum(_vol(i) for q in bx if (i := _inter(st_top, q))) / p["t"] * 0.01
                eq(on, laid, "bearing")
                eq(laid, (_vol(st_top) - sum(_vol(i) for h in notch if (i := _inter(st_top, h)))) / p["t"] * 0.01, "bearing")
            plank_vol[0] += sum(_vol(q) for q in bx)
        else:
            assert f"S_{name}" in objs, f"[count] S {name} missing"
            q = boxes(f"S_{name}_Conc")[0]
            assert abs(q[5] - s_["top"]) < 1e-5 and abs(q[5] - q[2] - s_["t"]) < 1e-5, f"[level] S {name}: z {q[2]:.3f}..{q[5]:.3f}"
            assert all(abs(q[i] - cl[j]) < 1e-5 for i, j in ((0, 0), (1, 1), (3, 2), (4, 3))), f"[position] S {name}: not between the beam faces"
            bars = _world_bars(objs[f"S_{name}_Bars"])
            Lc = (cl[2] - cl[0], cl[3] - cl[1])
            sa = 0 if Lc[0] <= Lc[1] + 1e-9 else 1
            zb = s_["top"] - s_["t"] + s_["cover"] + s_["d"] / 2
            zt = s_["top"] - s_["cover"] - s_["d"] / 2
            for b in bars:
                assert all(abs(v.z - zb) < 1e-5 or abs(v.z - zb - s_["d"]) < 1e-5 or abs(v.z - zt) < 1e-5 for v in b), \
                    f"[slab bars] S {name}: bar z {b[0].z:.4f} not at the cover"
            for ax, s, z in ((sa, s_["s_short"], zb), (1 - sa, s_["s_long"], zb + s_["d"])):
                run = sorted(b[0][1 - ax] for b in bars if abs(b[0].z - z) < 1e-5 and abs(b[0][1 - ax] - b[1][1 - ax]) < 1e-6)
                assert len(run) >= 2 and abs(run[0] - cl[1 - ax] - s_["first"]) < 1e-5 and \
                    abs(cl[3 - ax] - run[-1] - s_["first"]) < 1e-5 and max(b_ - a_ for a_, b_ in zip(run, run[1:])) <= s + 1e-5, \
                    f"[slab bars] S {name}: {'xy'[ax]} bars spacing / first"
    _each(panels, panel, "floor panels")
    # S bars total: hand formula
    exp = 0.0
    for _, k, rc in panels:
        if k != "S":
            continue
        cl = _inset(rc)
        Lc = (cl[2] - cl[0], cl[3] - cl[1])
        sa = 0 if Lc[0] <= Lc[1] + 1e-9 else 1
        npos = lambda w, s: math.ceil((w - 2 * s_["first"]) / s - 1e-9) + 1
        exp += npos(Lc[1 - sa], s_["s_short"]) * (Lc[sa] + 2 * s_["anchor"])
        exp += npos(Lc[sa], s_["s_long"]) * (Lc[1 - sa] + 2 * s_["anchor"])
        for ax in (0, 1):
            exp += 2 * npos(Lc[1 - ax], s_["s_top"]) * (s_["top_frac"] * Lc[sa] + s_["anchor"])
    eq(sum(g_("rebar", "S")["bars"]), exp, "rebar length")
    eq(g_("concrete", "S")["vol"], sum((c_[2] - c_[0]) * (c_[3] - c_[1]) * s_["t"] for _, k, rc in panels if k == "S"
                                       for c_ in (_inset(rc),)), "slab concrete")
    # topping: cell-count union of the grown PS panels × 0.10 − planks − column holes
    w = GBEAM["b"] / 2
    grown = [(rc[0] - w, rc[1] - w, GB_TOP, rc[2] + w, rc[3] + w, t["top"]) for _, k, rc in panels if k == "PS"]
    # column holes count only where they lie inside the footprint
    holes = (_col_squares() if t["holes"] else []) + _wet_cuts()
    net = _union_volume(grown + holes) - _union_volume(holes)    # vol(grown − holes − wet cuts)
    tb = g_("concrete", "TOP")["boxes"]
    assert tb and all(abs(q[5] - t["top"]) < 1e-5 for q in tb if q[5] > GB_TOP + p["t"] + 1e-5) and \
        max(q[5] for q in tb) <= FL2 + 1e-5 and min(q[2] for q in tb) >= GB_TOP - 1e-5, \
        f"[level] topping z {min(q[2] for q in tb):.3f}..{max(q[5] for q in tb):.3f} (FL2 {FL2})"
    eq(g_("concrete", "TOP")["vol"], net - plank_vol[0], "topping")
    for h in _wet_cuts():   # no topping on the wet side of a wall (the bath ledge)
        assert not any((i := _inter(h, q)) and _vol(i) > 1e-7 for q in tb), f"[ledge] topping on the wet side at {h[:2]}"
    if TOPPING["holes"]:
        for h in _col_squares():
            assert not any((i := _inter(h, q)) and _vol(i) > 1e-7 for q in tb), f"[holes] topping fills a column at {h[:2]}"
    # mesh: inside the cover, at its level, spacing ≤ s both ways
    fp = _footprint()
    mz, ms, mc = t["mesh_z"], t["mesh_s"], t["mesh_cover"]
    wires = _world_bars(objs["TOP_FL2_Mesh"])
    inside = lambda x, y: any(b[0] - 1e-6 <= x <= b[3] + 1e-6 and b[1] - 1e-6 <= y <= b[4] + 1e-6 for b in fp)
    for wv in wires:
        for v in wv:
            assert abs(v.z - mz) < 1e-5, f"[mesh] wire at z {v.z:.3f}"
            assert all(inside(v.x + dx, v.y + dy) for dx in (-mc + 1e-4, mc - 1e-4) for dy in (-mc + 1e-4, mc - 1e-4)), \
                f"[mesh] wire end ({v.x:.2f}, {v.y:.2f}) inside the {mc} cover"
    for eb_ in _erode(fp, mc):   # every part of the meshed area: wires both ways no further than ms apart
        for ax in (0, 1):
            ks = sorted({round(wv[0][1 - ax], 5) for wv in wires if abs(wv[0][1 - ax] - wv[1][1 - ax]) < 1e-6
                         and eb_[1 - ax] - 1e-6 <= wv[0][1 - ax] <= eb_[4 - ax] + 1e-6
                         and min(wv[0][ax], wv[1][ax]) <= eb_[ax] + 1e-6 and max(wv[0][ax], wv[1][ax]) >= eb_[ax + 3] - 1e-6})
            edges = [eb_[1 - ax]] + ks + [eb_[4 - ax]]
            assert max(b_ - a_ for a_, b_ in zip(edges, edges[1:])) <= ms + 1e-5,                 f"[mesh] {'xy'[ax]} wires further than {ms} apart near ({eb_[0]:.2f}, {eb_[1]:.2f})"
    # hook bars over the bearing beams
    hk = _world_bars(objs["TOP_FL2_Hooks"])
    exp_hooks = _hook_bars(panels)
    assert len(hk) == len(exp_hooks), f"[hooks] {len(hk)} hook bars, spec {len(exp_hooks)}"
    eq(sum(g_("rebar", "TOP")["bars"]), sum(math.dist(b_[0], b_[1]) for b_ in exp_hooks), "hooks")
    solids = [bx for rows in (rows_before, r) for (el, _), x in rows.items() if el != "excavation" for bx in x["boxes"]]
    clash = [(a_, b_) for a_, b_ in itertools.combinations(solids, 2) if (i := _inter(a_, b_)) and _vol(i) > 1e-6]
    assert not clash, f"[clash] {len(clash)} solid pairs share volume (floor vs earlier stages)"
    npl = sum(len(_ps_layout(rc)[1]) for _, k, rc in panels if k == "PS")
    return f"ST04 ok: {nps} PS + {ns} S panels, {npl} planks, {len(wires)} mesh wires, {len(hk)} hook bars"
