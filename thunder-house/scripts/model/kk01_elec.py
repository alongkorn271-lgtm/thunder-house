"""KK01 ST12a ไฟฟ้า – อุปกรณ์ (generic ST12, devices only) – exec'd after kk01_tiles.py, built after ST10 paint.

The practice: when the wiring method, switch / socket grade, consumer unit and AC are not chosen, build the devices from
the plans and list those questions; don't route conduit on assumptions. Symbols are read from the sheets' vectors
(EE-02 lights / switches / PB / FCU / CDU, EE-03 sockets; the pages are stored rotated: x = (X0 − v) / K,
y = (Y0 − u) / K, K = 28.3465 pt/m at 1:100, origin from the grid dimension ticks). Socket heights are read off the
EE-03 labels (vector text), switches +1.30 (EE-01), all above the finished floor in front (outside: the ground).
Wall devices: a plate on the nearest finished face found by rays ±x / ±y at the device height (the last paint coat or
the tile), checked against a typed side table. Downlights: 6" LED 12 W trims hanging 2 mm under the board face (clear
of both ceiling coats), moved across into the gap between the lower C-line runners (a 15 cm cut-out). Eave lights:
surface round LED 18 W under the soffit. FCU on the bedroom wall under the ceiling, CDU on the ground outside.
Objects (collection "KK01 ST12 Electrical"): EL_<kind>_<n> (+ _Lens for lights). Spec: ST12_elec_spec.md.
"""

EL_K = 28.3465
# EE-02 / EE-03 symbol centres (model x, y), read from the PDF vectors (scratch script in the spec)
EL_LIGHTS = [(0.49, 2.99), (0.70, 1.14), (1.19, 4.88), (1.19, 6.65), (1.86, 2.99), (2.95, 1.14), (2.95, 2.87), (3.76, 4.88),
             (3.76, 6.65), (3.83, 8.34), (4.24, 1.14), (4.24, 2.87), (4.30, 9.94), (4.30, 11.62), (6.08, 0.42), (6.08, 2.39),
             (6.08, 4.44), (6.08, 6.34), (6.08, 8.34), (6.55, 9.94), (6.55, 11.62), (8.34, 0.42), (8.34, 2.39), (8.34, 4.44),
             (8.34, 6.34), (8.34, 8.34), (8.81, 9.94), (8.81, 11.62), (10.26, 0.42), (10.26, 2.39), (10.26, 4.98), (10.26, 6.95),
             (11.21, 4.00), (12.24, 0.42), (12.24, 2.39), (12.24, 4.98), (12.24, 6.95), (12.60, 4.00)]
EL_EAVE = [(0.00, -0.47), (4.99, -0.47), (9.49, -0.47), (12.98, -0.47)]
# (x, y, gangs): EE-02 draws two switches at the front door at x 7.06 / 7.50 — the second over window W2: one 2-gang
# plate on the wall strip between D1 and W2 instead (x 6.915–7.405, centre 7.16; assumed, flagged); the one by D3
# at (8.31, 7.23) has only a concrete sliver between W1 and D3: round the corner onto the east wall (9.30, 7.15), flagged
EL_SWITCHES = [(2.30, 4.34, 1), (2.72, 3.52, 1), (4.73, 6.24, 1), (5.34, 2.85, 1), (7.16, 1.35, 2), (9.30, 7.15, 1),
               (9.26, 9.49, 1), (9.74, 5.76, 1), (9.99, 7.86, 1), (10.25, 3.31, 1), (10.79, 2.79, 1)]
EL_SOCKETS = [(-0.61, 0.04, 1.30), (0.45, 7.90, 1.30), (0.60, -0.40, 2.80), (0.26, 7.96, 2.80), (0.36, 6.76, 0.40),
              (0.39, 4.58, 0.40), (1.74, 0.27, 1.30), (2.66, 7.17, 0.40), (3.71, 8.02, 1.30), (3.97, 11.98, 1.30),
              (4.35, 4.33, 0.40), (4.67, 5.50, 0.40), (4.74, 2.05, 1.30), (5.14, 7.97, 2.80), (5.37, 2.12, 1.30),
              (5.58, 0.26, 2.80), (5.60, 5.37, 0.40), (5.85, 9.48, 1.30), (5.35, 7.17, 0.40), (7.00, 9.40, 0.40),
              (8.96, 6.08, 1.30), (8.98, 1.70, 1.30), (9.08, 0.63, 0.40), (9.16, 10.77, 1.30), (9.22, 9.51, 1.30),
              (10.02, 6.22, 0.40), (10.10, 7.95, 1.30), (11.24, 2.65, 0.40), (12.48, 7.20, 0.40), (12.67, 0.36, 0.40),
              (12.40, -0.48, 2.80), (12.73, 8.07, 2.80), (13.60, 0.07, 1.30), (12.50, 7.90, 1.30)]
# moved off openings (flagged): #21 y 2.40 → 1.70 (it stood in door D3 of the living / bed 3 wall), #26 x 10.99 → 10.10
# (on window W2 of the laundry wall); #1 / #33 at the rear corners (column + W4 on the side walls): round the
# corner onto the rear outside wall, x 0.45 / 12.50; #18 x 7.80 → 5.35 (under window W1: its chase would cross the window);
# #19 kitchen (8.63, 11.81) under W1 of wall A with no brick beside it → south wall x 7.00 (clear of D2's parked leaf); #2 / #30 at the front
# corners off the corner (x 0.22 → 0.60, 12.70 → 12.40): fed from the room inside beside the corner socket on the side wall
EL_WP_SOCKETS = (0, 1, 8, 26, 32, 33)
EL_FROM_GL = (2, 3, 13, 15, 30, 31)                    # the +2.80 points (outside / verandahs): from the ground (assumed —
                                                       # +2.80 over the rear verandah floor would be above its ceiling +3.10)                  # EE-03 "≡" symbol: 3-pin with a moisture cover (legend)
EL_PB = (5.20, 6.10, 1.80)                             # EE-02 แผงควบคุม PB, centre height assumed
EL_FLUO = (11.25, 7.75, 2.38)                          # EE-02 LED T8 1×18 W, surface on the laundry wall over W2's lintel
# water heaters (EE-01 legend H, +1.80; BOQ 2 points, not on the plan — user: recommend): one on each shower wall
EL_WH = [(0.40, 2.70, "bath1"), (12.60, 3.20, "bath2")]
# AC sized from the room (user: estimate): ≈ 800 BTU/m² (outside walls, sun) → bed1 17.2 m² 13,000, bed2 / bed3 10.3 m² 9,000
EL_BTU = dict(bed1=13000, bed2=9000, bed3=9000)
EL_AC = [dict(room="bed1", fcu=(1.09, 4.31), cdu=(-0.48, 5.81)), dict(room="bed2", fcu=(11.48, 4.70), cdu=(13.67, 5.97)),
         dict(room="bed3", fcu=(12.00, 2.78), cdu=(13.67, 1.50))]
EL = dict(sw=1.30, plate=(0.075, 0.12, 0.008), sock_plate=(0.12, 0.075, 0.008), reach=0.80,
          dl_trim=0.17, dl_cut=0.15, dl_t=0.012, dl_below=0.002, eave_d=0.30, eave_h=0.08,
          pb=(0.45, 0.40, 0.10), fluo=(0.62, 0.08, 0.06), fcu=(0.80, 0.29, 0.20), fcu_gap=0.10, cdu=(0.80, 0.55, 0.28),
          cdu_off=0.10, slide=0.60, margin=0.02)
# typed check table: the wall each device stands on (normal axis, side the plate faces) — read once off the build,
# then frozen here so a device that jumps to the next wall fails
EL_SIDES = {"EL_FLUO": (1, 1), "EL_PB": (0, 1), "EL_SO_00": (0, -1), "EL_SO_01": (1, 1), "EL_SO_02": (1, -1),
            "EL_SO_03": (1, 1), "EL_SO_04": (0, 1), "EL_SO_05": (0, 1), "EL_SO_06": (1, 1), "EL_SO_07": (1, -1),
            "EL_SO_08": (1, 1), "EL_SO_09": (1, -1), "EL_SO_10": (1, 1), "EL_SO_11": (0, -1), "EL_SO_12": (0,
            -1), "EL_SO_13": (1, 1), "EL_SO_14": (0, 1), "EL_SO_15": (0, 1), "EL_SO_16": (0, 1), "EL_SO_17": (1,
            1), "EL_SO_18": (1, -1), "EL_SO_19": (1, 1), "EL_SO_20": (0, -1), "EL_SO_21": (0, -1),
            "EL_SO_22": (1, -1), "EL_SO_23": (0, -1), "EL_SO_24": (0, -1), "EL_SO_25": (0, 1), "EL_SO_26": (1,
            1), "EL_SO_27": (1, -1), "EL_SO_28": (1, -1), "EL_SO_29": (0, -1), "EL_SO_30": (1, -1),
            "EL_SO_31": (1, 1), "EL_SO_32": (0, 1), "EL_SO_33": (1, 1), "EL_SW_00": (1, 1), "EL_SW_01": (0, 1),
            "EL_SW_02": (0, -1), "EL_SW_03": (0, 1), "EL_SW_04": (1, 1), "EL_SW_05": (0, -1), "EL_SW_06": (0,
            -1), "EL_SW_07": (0, 1), "EL_SW_08": (1, 1), "EL_SW_09": (1, 1), "EL_SW_10": (1, -1), "EL_WH_1": (1, 1), "EL_WH_2": (1, 1)}
C_ELEC = "KK01 ST12 Electrical"
STAGES.append(C_ELEC)


def _el_finish():
    """Boxes a ray may hit at device height: brick, ties, plaster, columns, wall tiles and the paint films."""
    out = list(_obstacles())
    for cn in (C_TILE, C_PAINT):
        c = bpy.data.collections.get(cn)
        if c:
            for o in c.objects:
                if o.type == "MESH" and o.data.get("element") not in ("excavation", "mesh") and \
                        (cn == C_PAINT or o.data.get("element") in ("wall_tile", "adhesive", "membrane", "step_tile", "riser_tile")):
                    bm = _world_bm(o)
                    try:
                        out += _obj_boxes(bm, o.name)
                    finally:
                        bm.free()
    return out


def _el_ray(boxes, x, y, z):
    """Nearest face from (x, y, z) along ±x / ±y: (distance, ax, plane, sg) — sg = the side the face looks to."""
    best = None
    for b in boxes:
        if not (b[2] <= z <= b[5]):
            continue
        for ax in (0, 1):
            o = 1 - ax
            p, q = (x, y)[ax], (x, y)[o]
            if not (b[o] < q < b[o + 3]):
                continue
            if b[ax] >= p:
                d, pl, sg = b[ax] - p, b[ax], -1
            elif b[ax + 3] <= p:
                d, pl, sg = p - b[ax + 3], b[ax + 3], 1
            else:
                continue
            if best is None or d < best[0]:
                best = (d, ax, pl, sg)
    return best


def _el_floor(x, y):
    """Finished floor under (x, y): the tile top there, else the ground."""
    tops = [b[5] for n, v in _ft_boxes().items() if n.endswith("_Tiles") or n.startswith("FT_Step_Treads") for b in v
            if b[0] <= x <= b[3] and b[1] <= y <= b[4]]
    return max(tops) if tops else GL


def _el_wall(boxes, x, y, h, size, flush=True, from_gl=False):
    """A plate (w along the wall, ht, t) for the symbol at (x, y): box, (ax, sg), floor base."""
    w, ht, t = size
    # the floor in front: try the symbol point, then 0.3 m round it (a symbol just outside its room's tile)
    base = GL if from_gl else _el_floor(x, y)
    z = base + h
    hit = _el_ray(boxes, x, y, z)
    assert hit and hit[0] <= EL["reach"], f"[wall] device at ({x}, {y}): no wall within {EL['reach']} m"
    _, ax, pl, sg = hit
    front = (x, y)
    P = [0.0, 0.0]
    P[ax], P[1 - ax] = pl + sg * 0.05, front[1 - ax]
    base = GL if from_gl else _el_floor(*P)
    z = base + h
    a, b = sorted((pl, pl + sg * t))
    u0 = front[1 - ax]
    hard = _el_hard() if flush else [b for (el, _), x_ in qto(C_WALL).items() if el == "opening" for b in x_["boxes"]]
    for k in range(int(EL["slide"] / 0.01) * 2 + 1):      # flush box into brick: slide off ties, columns, openings
        u = u0 + (k + 1) // 2 * 0.01 * (1 if k % 2 else -1)
        if not _el_blocked(hard, ax, pl, sg, u, z, w, ht) and _el_backed(boxes, ax, pl, sg, u, z, w, ht):
            break
    else:
        raise AssertionError(f"[tie] device at ({x}, {y}): no brick within {EL['slide']} m along the wall")
    box = (a, u - w / 2, z - ht / 2, b, u + w / 2, z + ht / 2) if ax == 0 else (u - w / 2, a, z - ht / 2, u + w / 2, b, z + ht / 2)
    return box, (ax, sg), base


def _el_backed(boxes, ax, pl, sg, u, z, w, ht):
    """The plate's back corners and centre all lie on a finished face (0.3 mm into it)."""
    d = pl - sg * 0.0003
    for du, dz in ((0, 0), (-w / 2 + 1e-3, -ht / 2 + 1e-3), (w / 2 - 1e-3, -ht / 2 + 1e-3), (-w / 2 + 1e-3, ht / 2 - 1e-3), (w / 2 - 1e-3, ht / 2 - 1e-3)):
        P = [0.0, 0.0, z + dz]
        P[ax], P[1 - ax] = d, u + du
        if not any(all(q[k] - 1e-6 <= P[k] <= q[k + 3] + 1e-6 for k in range(3)) for q in boxes):
            return False
    return True


def _el_hard():
    """Ties, columns and opening voids: where a flush box can't be cut in."""
    return [b for (el, _), x in qto(C_WALL).items() if el in ("concrete", "opening") for b in x["boxes"]] +         [b for (el, _), x in qto(C_COL).items() if el == "concrete" for b in x["boxes"]]


def _el_blocked(hard, ax, pl, sg, u, z, w, ht):
    """The box behind a plate (50 mm into the wall from the finish) meets a tie / column / opening (+ margin)."""
    m = EL["margin"]
    d0, d1 = sorted((pl - sg * 0.005, pl - sg * 0.06))
    q = (d0, u - w / 2 - m, z - ht / 2 - m, d1, u + w / 2 + m, z + ht / 2 + m) if ax == 0 else         (u - w / 2 - m, d0, z - ht / 2 - m, u + w / 2 + m, d1, z + ht / 2 + m)
    return any((i := _inter(q, h)) and min(i[k + 3] - i[k] for k in range(3)) > 1e-6 for h in hard)


def _el_runners():
    """Lower C-line runner plan rects (x0, y0, x1, y1) and the board under them: [(board box, [runner rects])]."""
    out = []
    for o in _coll(C_CEIL).objects:
        if o.type != "MESH" or o.data.get("element") not in ("ceiling", "soffit"):
            continue
        bm = _world_bm(o)
        try:
            boards = _obj_boxes(bm, o.name)
        finally:
            bm.free()
        fr = bpy.data.objects.get(o.name.replace("_Board", "_Frame"))
        frame = []
        if fr:
            bm = _world_bm(fr)
            try:
                frame = _obj_boxes(bm, fr.name)
            finally:
                bm.free()
        for b in boards:
            rs = [(f[0], f[1], f[3], f[4]) for f in frame if abs(f[2] - b[5]) < 1e-4 and f[0] < b[3] and f[3] > b[0] and f[1] < b[4] and f[4] > b[1]]
            out.append((b, rs))
    return out


def _el_light_at(x, y, boards):
    """(x, y) moved across into the nearest runner gap that clears the cut-out; the board above it."""
    r = EL["dl_cut"] / 2
    for b, rs in boards:
        if b[0] <= x <= b[3] and b[1] <= y <= b[4]:
            if not rs:
                return (x, y), b
            ax = 0 if (rs[0][2] - rs[0][0]) > (rs[0][3] - rs[0][1]) else 1    # runners along x → move in y
            o = 1 - ax
            near = sorted({(q[o], q[o + 2]) for q in rs if q[ax] <= (x, y)[ax] <= q[ax + 2]})
            p = (x, y)[o]
            best = None
            for (a0, a1), (b0, b1) in zip(near, near[1:]):
                if b0 - a1 >= 2 * r + 0.004:
                    c = min(max(p, a1 + r + 0.002), b0 - r - 0.002)
                    if best is None or abs(c - p) < abs(best - p):
                        best = c
            if best is None:
                return (x, y), b
            return ((x, best) if o == 1 else (best, y)), b
    return None, None


def _el_disc(name, x, y, z0, z1, d, m, segs=24, **props):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=d / 2, radius2=d / 2, depth=z1 - z0)
    for v in bm.verts:
        v.co.z += (z0 + z1) / 2
        v.co.x += x
        v.co.y += y
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m)
    for k, v in props.items():
        me[k] = v
    return me


def _el_layout():
    boxes = _el_finish()
    boards = _el_runners()
    dev = []
    for i, (x, y, g) in enumerate(EL_SWITCHES):
        b, side, base = _el_wall(boxes, x, y, EL["sw"], EL["plate"])
        dev.append(dict(name=f"EL_SW_{i:02d}", kind="switch", box=b, side=side, h=EL["sw"], base=base, src=(x, y), gangs=g))
    for i, (x, y, h) in enumerate(EL_SOCKETS):
        b, side, base = _el_wall(boxes, x, y, h, EL["sock_plate"], from_gl=i in EL_FROM_GL)
        dev.append(dict(name=f"EL_SO_{i:02d}", kind="socket_wp" if i in EL_WP_SOCKETS else "socket", box=b, side=side, h=h, base=base, src=(x, y)))
    for i, (x, y, room) in enumerate(EL_WH):
        b, side, base = _el_wall(boxes, x, y, 1.80, EL["sock_plate"])
        dev.append(dict(name=f"EL_WH_{i + 1}", kind="wh", box=b, side=side, h=1.80, base=base, src=(x, y)))
    x, y, h = EL_PB
    b, side, base = _el_wall(boxes, x, y, h, EL["pb"][:2] + (EL["pb"][2],))
    dev.append(dict(name="EL_PB", kind="pb", box=b, side=side, h=h, base=base, src=(x, y)))
    x, y, h = EL_FLUO
    b, side, base = _el_wall(boxes, x, y, h, EL["fluo"], flush=False)
    dev.append(dict(name="EL_FLUO", kind="fluo", box=b, side=side, h=h, base=base, src=(x, y)))
    lights = []
    for i, (x, y) in enumerate(EL_LIGHTS + EL_EAVE):
        p, bd = _el_light_at(x, y, boards)
        assert p, f"[lights] light {i} at ({x}, {y}) under no ceiling"
        lights.append(dict(name=f"EL_DL_{i:02d}" if i < len(EL_LIGHTS) else f"EL_EAVE_{i - len(EL_LIGHTS)}", kind="downlight" if i < len(EL_LIGHTS) else "eave",
                           at=p, z=bd[2] - EL["dl_below"], src=(x, y)))
    ac = []
    for a in EL_AC:
        x, y = a["fcu"]
        w, ht, t = EL["fcu"]
        ceil = min(bd[2] for bd, _ in boards if bd[0] <= x <= bd[3] and bd[1] <= y + 0.3 <= bd[4] or bd[0] <= x <= bd[3] and bd[1] <= y - 0.3 <= bd[4])
        b, side, base = _el_wall(boxes, x, y, ceil - EL["fcu_gap"] - ht / 2 - FL2, (w, ht, t), flush=False)
        b = (*b[:2], ceil - EL["fcu_gap"] - ht, *b[3:5], ceil - EL["fcu_gap"])
        hit = _el_ray(boxes, *a["cdu"], 1.0)
        _, ax, pl, sg = hit
        cw, ch, cd = EL["cdu"]
        u = a["cdu"][1 - ax]
        d0, d1 = sorted((pl + sg * EL["cdu_off"], pl + sg * (EL["cdu_off"] + cd)))
        cb = (d0, u - cw / 2, GL, d1, u + cw / 2, GL + ch) if ax == 0 else (u - cw / 2, d0, GL, u + cw / 2, d1, GL + ch)
        ac.append(dict(room=a["room"], fcu=b, fcu_side=side, cdu=cb))
    return dev, lights, ac


def build_elec():
    c = _clear(C_ELEC)
    white = mat("M_ElecPlate", (0.95, 0.95, 0.93), 0.4)
    grey = mat("M_ElecGrey", (0.55, 0.56, 0.58), 0.5)
    lens = mat("M_ElecLens", (1.0, 0.97, 0.88), 0.3)
    dev, lights, ac = _el_layout()
    for d in dev:
        o = bpy.data.objects.new(d["name"], _boxes_data(d["name"], [d["box"]], white if d["kind"] != "pb" else grey,
                                                         element="elec", type=d["kind"], h=d["h"], base=d["base"],
                                                         ax=d["side"][0], sg=d["side"][1], gangs=d.get("gangs", 0),
                                                         moved=abs(((d["box"][1] + d["box"][4]) / 2 if d["side"][0] == 0 else (d["box"][0] + d["box"][3]) / 2) - d["src"][1 - d["side"][0]])))
        c.objects.link(o)
    for L in lights:
        x, y = L["at"]
        d, t = (EL["dl_trim"], EL["dl_t"]) if L["kind"] == "downlight" else (EL["eave_d"], EL["eave_h"])
        c.objects.link(bpy.data.objects.new(L["name"], _el_disc(L["name"], x, y, L["z"] - t, L["z"], d, white, element="elec", type=L["kind"])))
        c.objects.link(bpy.data.objects.new(L["name"] + "_Lens", _el_disc(L["name"] + "_Lens", x, y, L["z"] - t - 0.001, L["z"] - t, d * 0.8, lens)))
    for a in ac:
        c.objects.link(bpy.data.objects.new(f"EL_FCU_{a['room']}", _boxes_data(f"EL_FCU_{a['room']}", [a["fcu"]], white, element="elec", type="fcu",
                                                                             ax=a["fcu_side"][0], sg=a["fcu_side"][1])))
        c.objects.link(bpy.data.objects.new(f"EL_CDU_{a['room']}", _boxes_data(f"EL_CDU_{a['room']}", [a["cdu"]], grey, element="elec", type="cdu")))
    for m in (lens,):
        if m.node_tree:
            bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if bsdf and "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = (1.0, 0.95, 0.85, 1.0)
                bsdf.inputs["Emission Strength"].default_value = 3.0
    bpy.context.view_layer.update()
    return len(dev) + len(lights)


def _el_bounds(o):
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    return tuple(min(v[k] for v in vs) for k in range(3)) + tuple(max(v[k] for v in vs) for k in range(3))


def elec_report():
    objs = [o for o in _coll(C_ELEC).objects if o.data and o.data.get("element") == "elec"]
    n = {}
    for o in objs:
        n[o.data["type"]] = n.get(o.data["type"], 0) + 1
    names = dict(downlight="โคมดาวน์ไลท์ฝังฝ้า LED 12 W (6\")", eave="โคมซาลาเปา LED 18 W ใต้ชายคา", fluo="โคมฟลูออเรสเซนต์ LED 1×18 W (ซักล้าง)",
                 switch="สวิตช์ทางเดียว (แผง; 12 ตัว)", socket="เต้ารับคู่ 3 ขา กันชื้น ฝังผนัง", socket_wp="เต้ารับ 3 ขา มีฝาปิดกันชื้น (ภายนอก / ซักล้าง)",
                 pb="ตู้ consumer unit Schneider Square D Classic 18 ช่อง (PB)", wh="จุดเครื่องทำน้ำอุ่น 4,500 W (+1.80, เบรกเกอร์กันดูด)", fcu="แฟนคอยล์แอร์ FCU (ตำแหน่งวาง; 13,000 / 9,000 / 9,000 BTU)", cdu="คอยล์ร้อนแอร์ CDU (ตำแหน่งวาง)")
    out = [f"{names.get(k, k)}: {v} ชุด" for k, v in sorted(n.items())]
    sh = [o for o in objs if o.data["type"] in ("socket", "socket_wp")]
    out.append("เต้ารับตามความสูง: " + " · ".join(f"+{h:.2f} {sum(1 for o in sh if abs(o.data['h'] - h) < 1e-6)} จุด"
                                                  for h in sorted({round(o.data['h'], 2) for o in sh})))
    out.append("ยังไม่ได้ทำ (รอคำตอบ): ท่อ / สาย / เบรกเกอร์ / กล่องต่อสาย / มิเตอร์ / สายเมน")
    return "\n".join(out)


# ---------------------------------------------------------------- ST12a selfcheck

def _check_elec(rows_before):
    """Read back: counts as the sheets; every wall device backs onto a finished face (last coat / tile) on its typed
    wall side, at its height over the finished floor in front, nothing in front of its face, clear of the openings;
    every downlight hangs 2 mm under its board, cut-out clear of the runners; FCU under its ceiling, CDU on the ground."""
    objs = {o.name: o for o in _coll(C_ELEC).objects}
    fails = []
    kinds = {}
    for o in objs.values():
        if o.data and o.data.get("element") == "elec":
            kinds[o.data["type"]] = kinds.get(o.data["type"], 0) + 1
    gangs = sum(o.data.get("gangs", 0) for o in objs.values() if o.data and o.data.get("type") == "switch")
    if gangs != sum(g for *_, g in EL_SWITCHES) or gangs != 12:
        fails.append(f"[count] {gangs} switch gangs, EE-02 has 12")
    want = dict(downlight=len(EL_LIGHTS), eave=len(EL_EAVE), switch=len(EL_SWITCHES), socket=len(EL_SOCKETS) - len(EL_WP_SOCKETS),
                socket_wp=len(EL_WP_SOCKETS), pb=1, fluo=1, fcu=len(EL_AC), cdu=len(EL_AC), wh=len(EL_WH))
    if kinds != want:
        fails.append(f"[count] devices {kinds} != EE-02/EE-03 {want}")
    fin = _el_finish()
    gf = _Grid(fin)
    opens = [b for (el, _), x in qto(C_WALL).items() if el == "opening" for b in x["boxes"]]
    hard = _el_hard()
    tiles = [b for n, v in _ft_boxes().items() if n.endswith("_Tiles") or n.startswith("FT_Step_Treads") for b in v]
    for n, o in sorted(objs.items()):
        dt = o.data.get("type") if o.data else None
        if dt not in ("switch", "socket", "socket_wp", "pb", "fluo", "fcu", "wh"):
            continue
        b = _el_bounds(o)
        ax, sg = o.data["ax"], o.data["sg"]
        if dt != "fcu" and EL_SIDES.get(n) != (ax, sg):
            fails.append(f"[side] {n}: on {'xy'[ax]}{'+-'[sg < 0]}, the typed table says {EL_SIDES.get(n)}")
        if o.data.get("ax") is None:
            continue
        back = b[ax] if sg > 0 else b[ax + 3]
        c = [(b[k] + b[k + 3]) / 2 for k in range(3)]
        pb_, pf = list(c), list(c)
        pb_[ax], pf[ax] = back - sg * 0.0003, (b[ax + 3] if sg > 0 else b[ax]) + sg * 0.003
        on = any(all(q[k] - 1e-6 <= pb_[k] <= q[k + 3] + 1e-6 for k in range(3)) for q in gf.near((*pb_, *pb_), 1e-3))
        u_ = (b[1] + b[4]) / 2 if ax == 0 else (b[0] + b[3]) / 2
        if not on or not _el_backed(fin, ax, back, sg, u_, c[2], (b[4] - b[1]) if ax == 0 else (b[3] - b[0]), b[5] - b[2]):
            fails.append(f"[wall] {n}: back not on a finished face")
        if any(all(q[k] < pf[k] < q[k + 3] for k in range(3)) for q in gf.near((*pf, *pf), 1e-3)):
            fails.append(f"[wall] {n}: something stands in front of it")
        if dt != "fcu":
            P = list(c[:2])
            P[ax] = back + sg * 0.05
            fl = max((q[5] for q in tiles if q[0] <= P[0] <= q[3] and q[1] <= P[1] <= q[4]), default=GL)
            if n.startswith("EL_SO_") and int(n[-2:]) in EL_FROM_GL:
                fl = GL
            h = EL["sw"] if dt == "switch" else EL_PB[2] if dt == "pb" else EL_FLUO[2] if dt == "fluo" else 1.80 if dt == "wh" else                 EL_SOCKETS[int(n[-2:])][2] if int(n[-2:]) < len(EL_SOCKETS) else None      # the spec, not the object's prop
            if h is None or abs(c[2] - (fl + h)) > 1e-4:
                fails.append(f"[height] {n}: centre +{c[2] - fl:.3f} over the floor {fl:.2f}, sheet +{h}")
        span = tuple((back - 0.2 if k == ax else back + 0.2 if k == ax + 3 else b[k]) for k in range(6))
        wall = [i for q in opens if (i := _inter(span, q)) and min(i[k + 3] - i[k] for k in range(3)) > 1e-6]
        if wall:
            fails.append(f"[opening] {n}: over an opening")
        u = (b[1] + b[4]) / 2 if ax == 0 else (b[0] + b[3]) / 2
        w_ = (b[4] - b[1]) if ax == 0 else (b[3] - b[0])
        if dt not in ("fcu", "fluo") and _el_blocked(hard, ax, back, sg, u, c[2], w_ - 2 * EL["margin"] + 2e-4, b[5] - b[2] - 2 * EL["margin"] + 2e-4):
            fails.append(f"[tie] {n}: its box would cut a tie / column / opening")
    # lights: 2 mm under the board, the cut-out clear of the runners, inside a board
    boards = _el_runners()
    for n, o in sorted(objs.items()):
        dt = o.data.get("type") if o.data else None
        if dt not in ("downlight", "eave"):
            continue
        b = _el_bounds(o)
        x, y = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
        bd = [(q, rs) for q, rs in boards if q[0] <= x <= q[3] and q[1] <= y <= q[4] and q[2] >= b[5] - 0.01]
        if not bd:
            fails.append(f"[lights] {n}: under no ceiling board")
            continue
        q, rs = min(bd, key=lambda t: t[0][2])
        if abs(q[2] - EL["dl_below"] - b[5]) > 1e-5:
            fails.append(f"[lights] {n}: top {b[5]:.4f}, board face {q[2]:.4f} − {EL['dl_below']}")
        if dt == "downlight":
            r = EL["dl_cut"] / 2
            hit = [s for s in rs if max(s[0] - x, 0, x - s[2]) ** 2 + max(s[1] - y, 0, y - s[3]) ** 2 < r * r]
            if hit:
                fails.append(f"[lights] {n}: cut-out over a C-line runner at ({x:.2f}, {y:.2f})")
        if n + "_Lens" not in objs:
            fails.append(f"[lights] {n}: no lens")
    for a in EL_AC:
        f, cd = objs.get(f"EL_FCU_{a['room']}"), objs.get(f"EL_CDU_{a['room']}")
        if f and cd:
            fb, cb = _el_bounds(f), _el_bounds(cd)
            ceil = min((q[2] for q, _ in boards if q[0] <= (fb[0] + fb[3]) / 2 <= q[3] and abs(q[1] + q[4] - fb[1] - fb[4]) < 99 and
                        q[1] - 0.4 <= (fb[1] + fb[4]) / 2 <= q[4] + 0.4), default=None)
            if ceil is None or fb[5] > ceil - EL["fcu_gap"] + 1e-5:
                fails.append(f"[ac] FCU {a['room']}: top {fb[5]:.3f} not {EL['fcu_gap']} under the ceiling")
            if abs(cb[2] - GL) > 1e-5:
                fails.append(f"[ac] CDU {a['room']}: not on the ground")
    # nothing inside a solid or a finish
    sol = fin + [b for (el, _), x in qto(C_COL).items() if el == "concrete" for b in x["boxes"]]
    gs = _Grid(sol)
    for n, o in objs.items():
        if o.data and o.data.get("element") == "elec":
            b = _el_bounds(o)
            s = (b[0] + 1e-4, b[1] + 1e-4, b[2] + 1e-4, b[3] - 1e-4, b[4] - 1e-4, b[5] - 1e-4)
            if any((i := _inter(s, q)) and min(i[k + 3] - i[k] for k in range(3)) > 1e-6 for q in gs.near(s)):
                fails.append(f"[clash] {n} inside a wall / finish")
    if fails:
        raise AssertionError(f"{len(fails)} failing in electrical:\n" + "\n".join(fails[:12]))
    return f"ST12a ok: " + " · ".join(f"{k} {v}" for k, v in sorted(kinds.items()))
