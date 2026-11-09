"""KK01 ST18 รายการย่อย (generic ST18 "the leftovers") – exec'd after kk01_sanitary.py, built last. The user (5 พ.ย. 69):
"เอาตามที่ recommend ในส่วนรายการย่อยที่ไม่ได้ทำ".
Modelled:
  - ผนังแบบ 4 กรุไม้เทียม (A-02) — A-06 draws it only on the front pier between D1 and W2: WPC battens 2.5 × 5 cm
    @7.5 cm vertical on 3 galvanised 1" box rails, 2 cm off the paint, from the verandah floor to the soffit;
  - W3 arched head (A-15): the arch as frame segments in the top of each W3 unit (the brick opening stays square);
  - shower screens (A-13 draws the 0.85 bay line): tempered glass 10 mm fixed, 0.80 out × 1.90 on a U channel;
  - laundry yard (A-04 outline x 10.6–13.1, y 9.3–11.3, kept off the beam's sand pad and the steps; A-02 FL1 พื้น ค.ส.ล. ผิวขัดหยาบ, used by no room): 0.10 slab
    on 0.05 sand, mesh 4 mm @0.20, top +0.10, openings over the septic lid and round the vent;
  - take-off from the model: corner beads (เซี้ยม) on every convex vertical plaster edge and opening edge, PVC
    trims on the wall tiles' convex edges.
Not modelled (recommend, in the spec): bath floor falls (in the screed), air chambers as pipe (counted), D1 lites / D4
louvres (in the door sets), nosing / skirting / gutters (not drawn).
Objects (collection "KK01 ST18 Extras"): EX_Clad_*, EX_Arch_*, EX_Screen_*, EX_Yard_*. Spec: ST18_extras_spec.md.
"""

EX = dict(batten=(0.025, 0.05), pitch=0.075, rail=0.025, off=0.020, screen=(0.80, 1.90, 0.010), yard=(10.66, 9.36, 13.13, 11.30),
          yard_t=0.10, yard_top=0.10, sand=0.05, lid=0.60, mesh_s=0.20)
C_EXTRA = "KK01 ST18 Extras"
STAGES.append(C_EXTRA)


def _ex_pier():
    """The verandah-side face of the Ga3-Ga5 pier between D1 and W2: (y face (paint), x0, x1, z0, z1)."""
    ops = {(o["tp"]): o for o in _un_openings() if o["wall"] == "Ga3-Ga5"}
    d1, w2 = ops["D1"]["box"], ops["W2"]["box"]
    x0, x1 = d1[3] + PLASTER["t"], w2[0] - PLASTER["t"]             # between the reveal plasters
    w = next(w for w in WALLS if _wl(w)[0] == "Ga3-Ga5")
    kc = _wl(w)[2]
    face = kc - BRICK["t"] / 2 - PLASTER["t"] - 3 * PAINT["film"]   # the verandah side (−y), on the last coat
    return face, x0, x1, FL_WET, _soffit_level()


def _ex_layout():
    L = dict(clad=[], rails=[], arch=[], screen=[], chan=[], yard=[], sand=[], mesh=[])
    face, x0, x1, z0, z1 = _ex_pier()
    bt, bw = EX["batten"]
    yb1 = face - EX["off"]
    n = int((x1 - x0 - bw) / EX["pitch"]) + 1
    s0 = x0 + (x1 - x0 - (n - 1) * EX["pitch"] - bw) / 2
    for i in range(n):
        a = s0 + i * EX["pitch"]
        L["clad"].append((a, yb1 - bt, z0 + 0.01, a + bw, yb1, z1 - 0.01))
    for zz in (z0 + 0.15, (z0 + z1) / 2, z1 - 0.15):
        L["rails"].append((x0 + 0.005, yb1, zz - EX["rail"] / 2, x1 - 0.005, face - 0.0005, zz + EX["rail"] / 2))
    # W3 arches: a half-ring of 9 segments under the frame head, spanning the inner width
    for op in _un_openings():
        if op["tp"] != "W3":
            continue
        T, g, f = PLASTER["t"], UN["gap"], UN["face"]
        b, ax, kc = op["box"], op["ax"], op["kc"]
        u0, u1 = b[ax] + T + g + f, b[ax + 3] - T - g - f
        zt = b[5] - T - g - f
        r = (u1 - u0) / 2
        cu, cz = (u0 + u1) / 2, zt - r
        for k in range(9):
            a0, a1 = math.pi * k / 9, math.pi * (k + 1) / 9
            pa = [(cu + r * math.cos(a), cz + r * math.sin(a)) for a in (a0, a1)]
            # the spandrel corner piece outside the arch, one per segment column (a filled stair under the head)
            ua, ub = sorted((pa[0][0], pa[1][0]))
            zlow = min(pa[0][1], pa[1][1])
            if zt - zlow > 0.004:
                L["arch"].append(_B(ax, ua, ub, kc - 0.02, kc + 0.02, zlow, zt))
    # shower screens: from the fixture wall at the bay line, 0.80 out, on the floor
    sw, sh, st = EX["screen"]
    for bath, x in (("bath1", 0.85), ("bath2", 12.15)):
        wy, nrm = SN_WALL[bath]
        y0, y1 = sorted((wy + nrm * 0.002, wy + nrm * (0.002 + sw)))
        L["screen"].append((x - st / 2, y0, FL_WET + 0.02, x + st / 2, y1, FL_WET + 0.02 + sh))
        L["chan"].append((x - 0.012, y0, FL_WET + 0.0005, x + 0.012, y1, FL_WET + 0.02))
    # laundry yard slab with the lid / vent openings
    yx0, yy0, yx1, yy1 = EX["yard"]
    zt, t = GL + EX["yard_top"], EX["yard_t"]
    tx, ty = SN_STRUCT["T2"]
    holes = [(tx - EX["lid"] / 2, ty - EX["lid"] / 2, tx + EX["lid"] / 2, ty + EX["lid"] / 2),
             (tx + 0.30 - 0.06, ty + 0.30 - 0.06, tx + 0.30 + 0.06, ty + 0.30 + 0.06)]
    for q in _rects_minus([(yx0, yy0, yx1, yy1)], holes):
        L["yard"].append((q[0], q[1], zt - t, q[2], q[3], zt))
        L["sand"].append((q[0], q[1], zt - t - EX["sand"], q[2], q[3], zt - t))
    L["mesh"] = _mesh_wires([(b[0] + 0.05, b[1] + 0.05, 0.0, b[3] - 0.05, b[4] - 0.05, 1.0) for b in L["yard"]
                             if b[3] - b[0] > 0.15 and b[4] - b[1] > 0.15], EX["mesh_s"], zt - t / 2)
    return L


def _ex_convex_edges(boxes, solids, step=0.05):
    """Length of the convex vertical edges of the boxes: at each 5 cm of an edge, exactly one of the four 5 mm
    quadrants round it is solid (the box's own)."""
    g = _Grid(solids)
    tot = 0.0
    seen = set()
    for b in boxes:
        for x in (b[0], b[3]):
            for y in (b[1], b[4]):
                key = (round(x, 4), round(y, 4))
                n = max(1, int((b[5] - b[2]) / step))
                for k in range(n):
                    z = b[2] + (k + 0.5) * (b[5] - b[2]) / n
                    zk = (key, round(z / step))
                    if zk in seen:
                        continue
                    occ = 0
                    for dx in (-0.005, 0.005):
                        for dy in (-0.005, 0.005):
                            P = (x + dx, y + dy, z)
                            if any(w[0] < P[0] < w[3] and w[1] < P[1] < w[4] and w[2] < P[2] < w[5] for w in g.near((*P, *P), 1e-3)):
                                occ += 1
                    if occ == 1:
                        seen.add(zk)
                        tot += (b[5] - b[2]) / n
    return tot


def build_extras():
    c = _clear(C_EXTRA)
    L = _ex_layout()
    wpc = mat("M_WPC_Wood", (0.45, 0.30, 0.18), 0.6)
    gi = mat("M_GI_Box", (0.70, 0.71, 0.72), 0.4, 0.8)
    alu = bpy.data.materials.get("M_AluBlack") or mat("M_AluBlack", (0.05, 0.05, 0.05), 0.35, 0.8)
    gl = _glass_mat()
    conc = mat("M_Concrete", (0.50, 0.50, 0.48), 0.85)
    sand = mat("M_Sand", (0.76, 0.68, 0.52), 0.95)
    steel = mat("M_Rebar", (0.28, 0.17, 0.11), 0.55, 0.6)
    parts = [("EX_Clad_Battens", L["clad"], wpc, dict(element="cladding", type="W4", th="ผนังแบบ 4 ไม้เทียม WPC 2.5×5 ซม. @7.5 ซม.")),
             ("EX_Clad_Rails", L["rails"], gi, dict(element="steel_rail", type="W4", th="โครงเหล็กกล่อง 1\" ยึดไม้เทียม")),
             ("EX_Arch_W3", L["arch"], alu, dict(element="arch", type="W3", th="หัวโค้ง W3 อลูมิเนียม")),
             ("EX_Screen_Glass", L["screen"], gl, dict(element="screen", type="SC", th="กระจกนิรภัย 10 มม. กั้นอาบน้ำ 0.80×1.90")),
             ("EX_Screen_Chan", L["chan"], alu, dict(element="screen_ch", type="SC", th="รางยูอลูมิเนียม")),
             ("EX_Yard_Conc", L["yard"], conc, dict(element="concrete", type="FL1", grade="St.240 ksc", th="ลานซักล้าง ค.ส.ล. ผิวขัดหยาบ (FL1) หนา 0.10")),
             ("EX_Yard_Sand", L["sand"], sand, dict(element="sand", type="FL1", th="ทรายรองลานซักล้าง 5 ซม."))]
    for n, boxes, m, props in parts:
        if boxes:
            c.objects.link(bpy.data.objects.new(n, _boxes_data(n, boxes, m, **props)))
    if L["mesh"]:
        c.objects.link(bpy.data.objects.new("EX_Yard_Mesh", _rebar_data("EX_Yard_Mesh", L["mesh"], 0.004, steel, element="mesh", type="FL1",
                                                                       th="ไวร์เมช 4 มม. @0.20", bar="Wire mesh 4 mm @0.20", dia_mm=4, spacing=EX["mesh_s"])))
    # take-off from the model: corner beads and tile trims
    plaster = qto(C_WALL)[("plaster", "PL")]["boxes"]
    solids_p = _obstacles() + [b for v in _ft_boxes().values() for b in v] + [b for (el, _), x in qto(C_COL).items() if el == "concrete" for b in x["boxes"]]
    q = bpy.data.objects.new("EX_Qty", None)
    horiz = sum(2 * (o["box"][o["ax"] + 3] - o["box"][o["ax"]] - 2 * PLASTER["t"]) * (1 if o["tp"].startswith("D") else 2)
                for o in _un_openings())                                # heads (+ sills), both faces
    q["bead_m"] = _ex_convex_edges(plaster, solids_p) + horiz
    q["bead_h"] = horiz
    wt = _ft_boxes("FT_Wall_Tiles").get("FT_Wall_Tiles", [])
    q["trim_m"] = _ex_convex_edges(wt, solids_p + wt) if wt else 0.0
    c.objects.link(q)
    bpy.context.view_layer.update()
    return len(L["clad"])


def extras_report():
    q = bpy.data.objects["EX_Qty"]
    face, x0, x1, z0, z1 = _ex_pier()
    L = _ex_layout()
    ya = sum((b[3] - b[0]) * (b[4] - b[1]) for b in L["yard"])
    out = [f"ผนังแบบ 4 ไม้เทียม WPC (เสาผนังหน้าบ้านระหว่าง D1–W2): {(x1 - x0) * (z1 - z0):.2f} ตร.ม. · ไม้ระแนง {len(L['clad'])} เส้น × {z1 - z0 - 0.02:.2f} ม."
           f" · เหล็กกล่อง 1\" {3 * (x1 - x0):.2f} ม.",
           f"หัวโค้ง W3: 2 ชุด (รวมในชุดหน้าต่าง)",
           f"กระจกนิรภัย 10 มม. กั้นอาบน้ำ 0.80×1.90: 2 บาน + รางยู {2 * EX['screen'][0]:.2f} ม.",
           f"ลานซักล้าง ค.ส.ล. FL1 หนา 0.10: {ya:.2f} ตร.ม. = {ya * EX['yard_t']:.3f} ลบ.ม. · ทราย {ya * EX['sand']:.3f} ลบ.ม. · ไวร์เมช {ya:.2f} ตร.ม.",
           f"เซี้ยมมุมปูนฉาบ (มุมนูนแนวดิ่งทุกมุม รวมขอบช่องเปิด): {q['bead_m']:.1f} ม. → {math.ceil(q['bead_m'] / 2.5 - 1e-9)} เส้น (2.5 ม.)",
           f"คิ้ว PVC มุมนอกกระเบื้องผนัง: {q['trim_m']:.1f} ม. → {math.ceil(q['trim_m'] / 2.4 - 1e-9) if q['trim_m'] else 0} เส้น (2.4 ม.)"]
    return "\n".join(out)


def _check_extras(rows_before):
    """Read back: battens on the pier face 2 cm off the paint, inside the pier, floor to soffit, at the pitch; screens on
    the floor from the fixture wall, clear of fixtures / tiles / doors; the yard at +0.10 with a lid opening over the
    septic tank, clear of the steps and the house; nothing inside a wall or a finish; the take-off positive."""
    objs = {o.name: o for o in _coll(C_EXTRA).objects}
    fails = []

    def boxes(n):
        if n not in objs:
            return []
        bm = _world_bm(objs[n])
        try:
            return _obj_boxes(bm, n)
        finally:
            bm.free()
    face, x0, x1, z0, z1 = _ex_pier()
    cl = sorted(boxes("EX_Clad_Battens"))
    if not cl:
        fails.append("[clad] no battens")
    else:
        if any(abs(b[4] - (face - EX["off"])) > 1e-4 for b in cl):
            fails.append(f"[clad] battens not {EX['off'] * 100:.0f} cm off the paint")
        if min(b[0] for b in cl) < x0 - 1e-4 or max(b[3] for b in cl) > x1 + 1e-4:
            fails.append("[clad] battens past the pier")
        if any(b[2] > z0 + 0.02 or b[5] < z1 - 0.02 for b in cl):
            fails.append("[clad] battens short of the floor / the soffit")
        gaps = [cl[i + 1][0] - cl[i][0] for i in range(len(cl) - 1)]
        if gaps and max(abs(gp - EX["pitch"]) for gp in gaps) > 1e-4:
            fails.append(f"[clad] batten pitch {max(gaps):.3f}, spec {EX['pitch']}")
    sc = boxes("EX_Screen_Glass")
    if len(sc) != 2:
        fails.append(f"[screen] {len(sc)} screens, A-13 one a bath")
    fx = []
    for o in _coll(C_SAN).objects:
        if o.data and o.data.get("element") == "fixture":
            bm = _world_bm(o)
            try:
                fx += _obj_boxes(bm, o.name)
            finally:
                bm.free()
    fin = _obstacles() + [b for v in _ft_boxes().values() for b in v]
    for b in sc:
        if abs(b[2] - (FL_WET + 0.02)) > 1e-4:
            fails.append("[screen] a screen off its channel on the floor")
        s = tuple(b[k] + 1e-4 for k in range(3)) + tuple(b[k] - 1e-4 for k in range(3, 6))
        if any((i := _inter(s, w)) and min(i[k + 3] - i[k] for k in range(3)) > 1e-6 for w in fx + fin):
            fails.append(f"[screen] a screen inside a fixture / wall / tile at x {b[0]:.2f}")
    yd = boxes("EX_Yard_Conc")
    if not yd or any(abs(b[5] - (GL + EX["yard_top"])) > 1e-5 or abs(b[5] - b[2] - EX["yard_t"]) > 1e-5 for b in yd):
        fails.append("[yard] yard slab missing or off +0.10 / 0.10")
    tx, ty = SN_STRUCT["T2"]
    h = EX["lid"] / 2 - 0.02                                   # the whole lid opening clear, not only its centre
    if any(b[0] < x < b[3] and b[1] < y < b[4] for b in yd for x in (tx - h, tx, tx + h) for y in (ty - h, ty, ty + h)):
        fails.append(f"[yard] no {EX['lid']:.2f} lid opening over the septic tank")
    house = [b for cn in (C_FOOT, C_STUB, C_GB, C_COL, C_FLOOR) for (el, _), x in qto(cn).items() if el != "excavation" for b in x["boxes"]] + \
        [b for n_, v in _ft_boxes("FT_Step").items() for b in v]
    for b in yd + boxes("EX_Yard_Sand"):
        if any((i := _inter(b, w)) and min(i[k + 3] - i[k] for k in range(3)) > 1e-6 for w in house):
            fails.append("[yard] the yard cuts the house / the steps")
            break
    for b in cl + boxes("EX_Clad_Rails") + boxes("EX_Arch_W3"):
        s = tuple(b[k] + 1e-4 for k in range(3)) + tuple(b[k] - 1e-4 for k in range(3, 6))
        if any((i := _inter(s, w)) and min(i[k + 3] - i[k] for k in range(3)) > 1e-6 for w in fin):
            fails.append(f"[clash] an extras piece inside a wall / finish at {tuple(round(v, 3) for v in b[:3])}")
            break
    q = bpy.data.objects.get("EX_Qty")
    if not q or q["bead_m"] <= 0 or q["trim_m"] <= 0:
        fails.append("[takeoff] corner beads / tile trims not measured")
    if fails:
        raise AssertionError(f"{len(fails)} failing in extras:\n" + "\n".join(fails[:12]))
    return f"ST18 ok: {len(cl)} battens, 2 screens, yard {len(yd)} pieces, beads {q['bead_m']:.1f} m, trims {q['trim_m']:.1f} m"
