"""KK01 ST14 ประตู หน้าต่าง (generic ST14) – exec'd after kk01_conduit.py, built last (after the paint and the electrics).

A-14 doors / A-15 windows, sizes = the units' overall frame (practice: brick = unit + 5 mm gap + 15 mm plaster a side, ST06
`UNIT_GAP`); every frame 2" × 4" (0.05 face × 0.10 deep = the plastered wall, flush with both plaster faces):
  D1 ไม้เนื้อแข็งบานเปิดคู่ ลูกฟักกระจกใส 5 มม. 1.80 × 2.15 (front, into the living room)
  D2 uPVC บานเลื่อน 1.00 × 2.00 (kitchen → verandah / laundry; A-04 "SLIDE"): the leaf hung on a track on the kitchen
     face, sliding over the wall
  D3 uPVC บานเปิด 0.90 × 2.00 ×5, lever handle;  D4 uPVC บานเปิด ห้องน้ำ (เกล็ดล่าง) 0.80 × 2.05 ×2, bath knob
  W1 / W2 อลูมิเนียมดำบานเลื่อน (4 panes F-S-S-F / 2 panes): fixed outside, sliders on the room side (practice)
  W3 อลูมิเนียมดำบานเปิดคู่ 8 ช่อง (the arch head not modelled: a rectangle), W4 บานเปิดเดี่ยว, W5 บานกระทุ้ง
  W6 ไม้เนื้อแข็งบานเลื่อน 2 บาน ลูกฟักไม้ (no glass)
Hinged doors open into the room they serve (table), the latch on the side of that room's switch (practice), else the
hinge by the nearer corner; leaves 10 mm over the finished floor, 3 mm off the jambs. No insect screens, no burglar bars
(neither drawn). Objects (collection "KK01 ST14 Units"): UN_<tp>_<wall>_<i>_{Frame, Leaf, Sash, Glass, Hw}.
Spec: ST14_units_spec.md.
"""

UN = dict(face=0.05, depth=0.10, gap=UNIT_GAP, sash=(0.038, 0.05), glass=0.005, leaf_gap=0.003, floor_gap=0.010,
          leaf_t=dict(D1=0.038, D2=0.035, D3=0.035, D4=0.035), hinges=3, pack=2, track=(0.06, 0.04))
UN_KIND = dict(D1=("door2", "ไม้เนื้อแข็ง"), D2=("slide_door", "uPVC"), D3=("door", "uPVC"), D4=("door", "uPVC"),
               W1=("slide4", "อลูมิเนียมดำ"), W2=("slide2", "อลูมิเนียมดำ"), W3=("casement2", "อลูมิเนียมดำ"),
               W4=("casement1", "อลูมิเนียมดำ"), W5=("awning", "อลูมิเนียมดำ"), W6=("slide2_wood", "ไม้เนื้อแข็ง"))
# hinged doors: the room each opens into (a point in it)
UN_SWING = {("C3-G3", 6.95): (3.0, 6.0), ("C3-G3", 3.40): (4.2, 2.0), ("C5-G5", 5.20): (11.0, 6.0), ("C5-G5", 2.43): (11.0, 1.5),
            ("C1-C6", 8.80): (8.8, 6.0), ("Ga3-Ga5", 6.00): (6.0, 3.0), ("E1a-Gb1a", 2.985): (1.2, 3.2), ("D5-D6", 10.89): (10.9, 3.6)}
C_UNIT = "KK01 ST14 Units"
STAGES.append(C_UNIT)


def _un_openings():
    """[dict(tp, wall, ax, kc, box (brick), u0, u1, z0, z1, ext sign or 0)] read from the walls' opening objects."""
    out = []
    for w in WALLS:
        name, ax, kc, u0, u1, flush, lean, ops, k, *_ = _wl(w)
        o = bpy.data.objects.get(f"WL_{name}_Open")
        boxes = []
        if o:
            bm = _world_bm(o)
            try:
                boxes = _obj_boxes(bm, o.name)
            finally:
                bm.free()
        for i, (tp, c) in enumerate(ops):
            b = min(boxes, key=lambda q: abs((q[ax] + q[ax + 3]) / 2 - c))
            assert abs((b[ax] + b[ax + 3]) / 2 - c) < 0.03, f"[count] {name}: no opening for {tp} at {c}"
            out.append(dict(tp=tp, wall=name, c=c, i=i, ax=ax, kc=kc, box=b, ext=flush))
    return out


def _un_floor(x, y):
    tops = [b[5] for n, v in _ft_boxes().items() if n.endswith("_Tiles") for b in v if b[0] <= x <= b[3] and b[1] <= y <= b[4]]
    return max(tops) if tops else FL2


def _B(ax, u0, u1, v0, v1, z0, z1):
    return (u0, v0, z0, u1, v1, z1) if ax == 0 else (v0, u0, z0, v1, u1, z1)


def _un_layout():
    """Per opening: the unit's boxes by part, and its props."""
    T, f, dp, g = PLASTER["t"], UN["face"], UN["depth"], UN["gap"]
    sw = [o for o in _coll(C_ELEC).objects if o.data and o.data.get("type") == "switch"]
    units = []
    for op in _un_openings():
        tp, ax, kc, b = op["tp"], op["ax"], op["kc"], op["box"]
        kind = UN_KIND[tp][0]
        door = tp.startswith("D")
        u0, u1 = b[ax] + T + g, b[ax + 3] - T - g                  # the unit's outer edges along the wall
        v0, v1 = kc - dp / 2, kc + dp / 2
        cx = ((u0 + u1) / 2, kc) if ax == 0 else (kc, (u0 + u1) / 2)
        z1 = b[5] - T - g
        z0 = _un_floor(*cx) if door else b[2] + T + g
        parts = dict(frame=[], leaf=[], sash=[], glass=[], hw=[], track=[])
        B = lambda a0, a1, c0, c1, e0, e1: _B(ax, a0, a1, c0, c1, e0, e1)
        parts["frame"] += [B(u0, u0 + f, v0, v1, z0, z1), B(u1 - f, u1, v0, v1, z0, z1), B(u0 + f, u1 - f, v0, v1, z1 - f, z1)]
        if not door:
            parts["frame"].append(B(u0 + f, u1 - f, v0, v1, z0, z0 + f))
        iu0, iu1, iz0, iz1 = u0 + f, u1 - f, (z0 if door else z0 + f), z1 - f
        ext = op["ext"] or 0
        vo = (lambda d0, d1: (kc + ext * d0, kc + ext * d1)) if ext else (lambda d0, d1: (kc + d0, kc + d1))
        info = dict(tp=tp, wall=op["wall"], c=op["c"], i=op["i"], ax=ax, kc=kc, kind=kind, outer=(u0, u1, z0, z1),
                    v=(v0, v1), ext=ext, door=door, hinge=None, into=None, leaf_w=0.0)
        sa, sd = UN["sash"]

        def sash(a0, a1, c0, c1, e0, e1, glass=True):
            """A sash ring + its glass (5 mm, centred in the ring's depth)."""
            parts["sash"] += [B(a0, a0 + sa, c0, c1, e0, e1), B(a1 - sa, a1, c0, c1, e0, e1),
                              B(a0 + sa, a1 - sa, c0, c1, e0, e0 + sa), B(a0 + sa, a1 - sa, c0, c1, e1 - sa, e1)]
            if glass:
                m = (c0 + c1) / 2
                parts["glass"].append(B(a0 + sa, a1 - sa, m - UN["glass"] / 2, m + UN["glass"] / 2, e0 + sa, e1 - sa))
            else:
                parts["sash"].append(B(a0 + sa, a1 - sa, (c0 + c1) / 2 - 0.006, (c0 + c1) / 2 + 0.006, e0 + sa, e1 - sa))
        if kind in ("slide4", "slide2", "slide2_wood"):
            n = 4 if kind == "slide4" else 2
            W = iu1 - iu0
            pw = (W + (n - 1) * sa) / n                                     # panes lap one stile where they meet
            # depth tracks: outside half and room half of the frame (interior walls: arbitrary sides)
            outs, ins = sorted(vo(0.0, sd)), sorted(vo(-sd, 0.0))
            for k in range(n):
                a0 = iu0 + k * (pw - sa)
                fixed = kind == "slide4" and k in (0, n - 1)
                track = outs if (fixed or (kind != "slide4" and k == 0)) else ins
                sash(a0, a0 + pw, track[0] + 0.002, track[1] - 0.002, iz0, iz1, glass=kind != "slide2_wood")
            info["panes"] = n
        elif kind in ("casement2", "casement1", "awning"):
            n = 2 if kind == "casement2" else 1
            W = (iu1 - iu0) / n
            c0, c1 = vo(-0.02, 0.02)
            c0, c1 = sorted((c0, c1))
            for k in range(n):
                a0 = iu0 + k * W
                sash(a0 + 0.002, a0 + W - 0.002, c0, c1, iz0 + 0.002, iz1 - 0.002)
                if kind == "casement2":                                     # 4 lites a leaf: glazing bars
                    for j in (1, 2, 3):
                        zz = iz0 + (iz1 - iz0) * j / 4
                        parts["sash"].append(B(a0 + 0.002 + sa, a0 + W - 0.002 - sa, c0 + 0.010, c1 - 0.010, zz - 0.012, zz + 0.012))
            info["panes"] = n
        elif kind in ("door", "door2"):
            lt = UN["leaf_t"][tp]
            into = UN_SWING.get((op["wall"], op["c"]))
            assert into, f"[swing] no swing room for {tp} on {op['wall']} at {op['c']}"
            side = 1 if (into[1 - ax] if ax == 0 else into[0]) > kc else -1     # the room's side across the wall
            side = 1 if ((into[1] if ax == 0 else into[0]) > kc) else -1
            # leaf on the room-side face of the frame rebate
            lv0, lv1 = sorted((kc + side * (dp / 2 - lt), kc + side * dp / 2))
            lz0, lz1 = z0 + UN["floor_gap"], iz1 - UN["leaf_gap"]
            la, lb = iu0 + UN["leaf_gap"], iu1 - UN["leaf_gap"]
            if kind == "door2":
                mid = (la + lb) / 2
                leaves = [(la, mid - 0.0015), (mid + 0.0015, lb)]
            else:
                leaves = [(la, lb)]
            # hinge side: latch by the room's switch on this wall (within 0.6 m of the jamb), else the hinge at the
            # end nearer a corner
            hinge = None
            for s_ in sw:
                sb = _el_bounds(s_)
                su = (sb[ax] + sb[ax + 3]) / 2
                sv = (sb[1 - ax] + sb[4 - ax]) / 2
                if (sv - kc) * side > 0 and abs(sv - kc) < 0.15 and min(abs(su - u0), abs(su - u1)) < 0.6:
                    hinge = "a" if abs(su - u1) < abs(su - u0) else "b"          # latch at the switch end
            if hinge is None:
                hinge = "a" if (u0 - op["box"][ax]) >= 0 and abs(u0 - _un_corner(op, -1)) < abs(u1 - _un_corner(op, 1)) else "b"
            info.update(hinge=hinge, into=side, leaf_w=(leaves[0][1] - leaves[0][0]), leaves=leaves, leaf_v=(lv0, lv1), leaf_z=(lz0, lz1))
            for a0, a1 in leaves:
                parts["leaf"].append(B(a0, a1, lv0, lv1, lz0, lz1))
                if kind == "door2" or tp == "D1":                             # glazed panel in each leaf
                    m = (lv0 + lv1) / 2
                    parts["glass"].append(B(a0 + 0.10, a1 - 0.10, m - UN["glass"] / 2 - 0.0002, m + UN["glass"] / 2 + 0.0002, lz0 + 0.30, lz1 - 0.20))
            # handle on the room face at the latch edge, 1.00 over the floor
            for j, (a0, a1) in enumerate(leaves):
                latch = (a1 - 0.07) if (kind == "door2" and j == 0) or (kind != "door2" and hinge == "a") else (a0 + 0.07)
                if kind == "door2" and j == 1:
                    latch = a0 + 0.07
                hv0, hv1 = sorted((kc + side * dp / 2, kc + side * (dp / 2 + 0.06)))
                parts["hw"].append(B(latch - 0.012, latch + 0.012, hv0, hv1, z0 + 0.98, z0 + 1.02))
        elif kind == "slide_door":
            # the leaf on a track on one face, 2 cm off the finish, lapping the opening 5 cm a side; the kitchen face first,
            # else the other one, sliding the way the wall is free (no column / wall in the run, no device behind the parked leaf)
            pref = 1 if op["wall"] == "B2-B5" else -1                   # the kitchen side of each D2 wall
            lt = UN["leaf_t"][tp]
            tw, th = UN["track"]
            la, lb = u0 - 0.05, u1 + 0.05
            lz0, lz1 = z0 + UN["floor_gap"], z1 + 0.02
            L_ = lb - la
            obst = _obstacles()
            devs = [_el_bounds(o_) for o_ in _coll(C_ELEC).objects if o_.data and o_.data.get("element") == "elec"]
            pick = None
            for side in (pref, -pref):
                face = kc + side * (dp / 2 + 0.0015 * 3 + 0.020)
                lv0, lv1 = sorted((face, face + side * lt))
                tv0, tv1 = sorted((face, face + side * tw))
                for dn in (-1, 1):
                    pa, pb = (la - L_, la) if dn < 0 else (lb, lb + L_)
                    run = B(min(la, pa), max(lb, pb), min(tv0, lv0), max(tv1, lv1), lz0, lz1 + 0.005 + th)
                    if any((i := _inter(run, w)) and min(i[k + 3] - i[k] for k in range(3)) > 1e-6 for w in obst):
                        continue
                    if any(d[ax] < pb and d[ax + 3] > pa and (((d[1] + d[4]) / 2 if ax == 0 else (d[0] + d[3]) / 2) - kc) * side > 0 and
                           abs(((d[1] + d[4]) / 2 if ax == 0 else (d[0] + d[3]) / 2) - kc) < 0.12 for d in devs):
                        continue
                    pick = (side, dn, lv0, lv1, tv0, tv1)
                    break
                if pick:
                    break
            assert pick, f"[slide] {op['wall']} {tp}: no free wall to slide on"
            side, dirn, lv0, lv1, tv0, tv1 = pick
            parts["leaf"].append(B(la, lb, lv0, lv1, lz0, lz1))
            ta, tb = (la - L_, lb) if dirn < 0 else (la, lb + L_)
            parts["track"].append(B(ta, tb, tv0, tv1, lz1 + 0.005, lz1 + 0.005 + th))
            info.update(into=side, leaf_w=L_, slide=(la, lb, dirn), leaf_v=(lv0, lv1), leaf_z=(lz0, lz1))
        units.append((info, parts))
    return units


def _un_corner(op, sgn):
    """The nearest wall end / column face along the wall from the opening, toward sgn."""
    b, ax = op["box"], op["ax"]
    return b[ax] - 1.0 if sgn < 0 else b[ax + 3] + 1.0


def _glass_mat():
    m = mat("M_Glass5", (0.85, 0.92, 0.95), 0.0)
    m.diffuse_color = (0.85, 0.92, 0.95, 0.25)
    if m.node_tree:
        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b:
            for k, v in (("Transmission Weight", 1.0), ("IOR", 1.52), ("Roughness", 0.0)):
                if k in b.inputs:
                    b.inputs[k].default_value = v
    for k, v in (("use_raytrace_refraction", True),):
        if hasattr(m, k):
            setattr(m, k, v)
    if hasattr(m, "thickness_mode"):
        m.thickness_mode = "SLAB"
    return m


def build_units():
    c = _clear(C_UNIT)
    alu = mat("M_AluBlack", (0.05, 0.05, 0.05), 0.35, 0.8)
    wood = mat("M_Hardwood", (0.40, 0.24, 0.13), 0.55)
    upvc = mat("M_uPVC", (0.92, 0.91, 0.88), 0.45)
    steel = mat("M_Hardware", (0.75, 0.75, 0.76), 0.3, 0.9)
    gl = _glass_mat()
    for info, parts in _un_layout():
        mtl = UN_KIND[info["tp"]][1]
        m = wood if "ไม้" in mtl else alu if "อลู" in mtl else upvc
        base = f"UN_{info['tp']}_{info['wall']}_{info['i']}"
        props = dict(tp=info["tp"], wall=info["wall"], c=info["c"], kind=info["kind"], ax=info["ax"], kc=info["kc"])
        for key, mm, el in (("frame", m, "frame"), ("sash", m, "sash"), ("leaf", m, "door_leaf"), ("glass", gl, "glass"),
                            ("hw", steel, "hardware"), ("track", steel, "hardware")):
            if parts[key]:
                o = bpy.data.objects.new(f"{base}_{key.capitalize()}", _boxes_data(f"{base}_{key.capitalize()}", parts[key], mm,
                                                                                element=el, type=info["tp"], th=f"{info['tp']} {mtl}", **props))
                if key == "leaf":
                    for k in ("hinge", "into", "leaf_w"):
                        if info.get(k) is not None:
                            o.data[k] = info[k]
                    if "slide" in info:
                        o.data["slide"] = list(info["slide"])
                c.objects.link(o)
    bpy.context.view_layer.update()
    return len(_un_openings())


def units_report():
    ops = _un_openings()
    n = {}
    for o in ops:
        n[o["tp"]] = n.get(o["tp"], 0) + 1
    names = {"D1": "ประตูไม้เนื้อแข็งบานเปิดคู่ ลูกฟักกระจก 1.80×2.15", "D2": "ประตู uPVC บานเลื่อน (รางแขวนหน้าผนัง) 1.00×2.00",
             "D3": "ประตู uPVC บานเปิด 0.90×2.00 + มือจับก้านโยก", "D4": "ประตู uPVC ห้องน้ำ (เกล็ดล่าง) 0.80×2.05 + ลูกบิดห้องน้ำ",
             "W1": "หน้าต่างอลูมิเนียมดำ บานเลื่อน 4 บาน (F-S-S-F) 2.40×1.20", "W2": "หน้าต่างอลูมิเนียมดำ บานเลื่อน 2 บาน 1.40×1.20",
             "W3": "หน้าต่างอลูมิเนียมดำ บานเปิดคู่ 8 ช่อง 1.00×1.90 (หัวโค้งตามแบบ)", "W4": "หน้าต่างอลูมิเนียมดำ บานเปิด 0.60×1.55",
             "W5": "หน้าต่างอลูมิเนียมดำ บานกระทุ้ง 0.80×0.50", "W6": "หน้าต่างไม้เนื้อแข็ง บานเลื่อน 2 บาน 2.60×1.20"}
    out = [f"{names[k]}: {v} ชุด" for k, v in sorted(n.items())]
    r = qto(C_UNIT)
    ga = sum(max((b[3] - b[0]) * (b[5] - b[2]), (b[4] - b[1]) * (b[5] - b[2])) for (el, _), x in r.items() if el == "glass" for b in x["boxes"])
    out.append(f"กระจกใส 5 มม.: {ga:.2f} ตร.ม.")
    hinged = sum(v * (2 if k == "D1" else 1) for k, v in n.items() if k in ("D1", "D3", "D4"))
    hn = hinged * UN["hinges"]
    out.append(f"บานพับสแตนเลส 4\": {hn} ตัว → {math.ceil(hn / UN['pack'] - 1e-9)} แพ็ค ({UN['pack']} ตัว) · กันชนประตู {hinged} ตัว · "
               f"รางบานเลื่อน D2 {n.get('D2', 0)} ชุด · กลอนบานคู่ D1 {n.get('D1', 0)} ชุด")
    per = sum(2 * ((o["box"][o["ax"] + 3] - o["box"][o["ax"]]) + (o["box"][5] - o["box"][2])) for o in ops if UN_KIND[o["tp"]][1] == "อลูมิเนียมดำ")
    out.append(f"ซิลิโคนยาแนวรอบวงกบอลูมิเนียม (2 ด้าน): {2 * per:.1f} ม.")
    return "\n".join(out)


# ---------------------------------------------------------------- ST14 selfcheck

def _check_units(rows_before):
    """Read back: one unit per opening, each frame snug in its plastered opening (5 mm a side) and flush with both
    plaster faces, nothing inside the walls / finishes / devices / ceilings, glass bounded by its sash and the right
    material, fixed panes outside, door leaves 10 mm over the floor, hinged leaves swinging clear into their room with
    the latch by the switch, the sliding leaf's run clear."""
    objs = {o.name: o for o in _coll(C_UNIT).objects}
    fails = []
    ops = _un_openings()
    kinds = {}
    for o in ops:
        kinds[o["tp"]] = kinds.get(o["tp"], 0) + 1
    if kinds != OPENING_COUNT:
        fails.append(f"[count] openings {kinds} != A-04 {OPENING_COUNT}")

    def boxes(n):
        if n not in objs:
            return []
        bm = _world_bm(objs[n])
        try:
            return _obj_boxes(bm, n)
        finally:
            bm.free()
    T, g = PLASTER["t"], UN["gap"]
    solids = _obstacles() + [b for n, v in _ft_boxes().items() for b in v] + \
        [b for (el, _), x in qto(C_CEIL).items() if el in ("ceiling", "soffit") for b in x["boxes"]]
    for o in _coll(C_PAINT).objects:
        if o.type == "MESH":
            bm = _world_bm(o)
            try:
                solids += _obj_boxes(bm, o.name)
            finally:
                bm.free()
    devs = [_el_bounds(o) for o in _coll(C_ELEC).objects if o.data and o.data.get("element") == "elec"]
    gs = _Grid(solids + devs)
    gm = bpy.data.materials.get("M_Glass5")
    if not gm or abs(gm.diffuse_color[3] - 0.25) > 1e-6:
        fails.append("[glass] glass material missing or opaque in solid view")
    else:
        bsdf = next((n for n in gm.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if gm.node_tree else None
        if bsdf and ("Transmission Weight" in bsdf.inputs and abs(bsdf.inputs["Transmission Weight"].default_value - 1) > 1e-6 or
                     abs(bsdf.inputs["IOR"].default_value - 1.52) > 1e-6):
            fails.append("[glass] glass not transmissive / IOR 1.52")
    for op in ops:
        tp, ax, kc, b = op["tp"], op["ax"], op["kc"], op["box"]
        base = f"UN_{tp}_{op['wall']}_{op['i']}"
        fr = boxes(base + "_Frame")
        if not fr:
            fails.append(f"[count] {base}: no frame")
            continue
        lo = min(q[ax] for q in fr)
        hi = max(q[ax + 3] for q in fr)
        zt = max(q[5] for q in fr)
        if abs(lo - (b[ax] + T + g)) > 1e-4 or abs(hi - (b[ax + 3] - T - g)) > 1e-4 or abs(zt - (b[5] - T - g)) > 1e-4:
            fails.append(f"[snug] {base}: frame {lo:.3f}..{hi:.3f} top {zt:.3f}, opening less plaster + {g * 1000:.0f} mm "
                         f"{b[ax] + T + g:.3f}..{b[ax + 3] - T - g:.3f} top {b[5] - T - g:.3f}")
        size = OPENINGS[tp]
        if abs((hi - lo) - size[0]) > 1e-4:
            fails.append(f"[snug] {base}: unit {hi - lo:.3f} wide, A-14/15 {size[0]}")
        if not tp.startswith("D"):
            zb = min(q[2] for q in fr)
            if abs(zb - (b[2] + T + g)) > 1e-4 or abs((zt - zb) - size[1]) > 1e-4:
                fails.append(f"[snug] {base}: window {zt - zb:.3f} high from {zb:.3f}, A-15 {size[1]}")
        v0 = min(q[1 - ax] if ax == 0 else q[0] for q in fr) if False else min(q[4 - 3 * (ax == 1) - 3 + 3 * 0] for q in fr) if False else \
            min((q[1] if ax == 0 else q[0]) for q in fr)
        v1 = max((q[4] if ax == 0 else q[3]) for q in fr)
        if abs(v0 - (kc - UN["depth"] / 2)) > 1e-4 or abs(v1 - (kc + UN["depth"] / 2)) > 1e-4:
            fails.append(f"[snug] {base}: frame depth {v0:.3f}..{v1:.3f}, plaster faces {kc - 0.05:.3f}..{kc + 0.05:.3f}")
        allp = fr + boxes(base + "_Sash") + boxes(base + "_Leaf") + boxes(base + "_Glass") + boxes(base + "_Hw") + boxes(base + "_Track")
        for q in allp:
            s = tuple(q[k] + 1e-4 for k in range(3)) + tuple(q[k] - 1e-4 for k in range(3, 6))
            hit = [w for w in gs.near(s) if (i := _inter(s, w)) and min(i[k + 3] - i[k] for k in range(3)) > 1e-6]
            if hit:
                fails.append(f"[clash] {base}: a piece inside a wall / finish / device at {tuple(round(v, 3) for v in q[:3])}")
                break
        # glass bounded by its sash / leaf (all six sides inside the unit's frame box)
        env = (min(q[0] for q in fr), min(q[1] for q in fr), min(q[2] for q in fr), max(q[3] for q in fr), max(q[4] for q in fr), max(q[5] for q in fr))
        for q in boxes(base + "_Glass"):
            if not all(env[k] - 1e-5 <= q[k] and q[k + 3] <= env[k + 3] + 1e-5 for k in range(3)):
                fails.append(f"[glass] {base}: a pane outside its frame")
                break
            th = min(q[k + 3] - q[k] for k in range(3))
            if abs(th - UN["glass"]) > 5e-4:
                fails.append(f"[glass] {base}: pane {th * 1000:.1f} mm, spec {UN['glass'] * 1000:.0f}")
                break
        kind = UN_KIND[tp][0]
        if kind == "slide4" and op["ext"]:
            sa = boxes(base + "_Sash")
            # end panes (fixed) on the outside half, middle panes on the room half
            u_sorted = sorted({round(q[ax], 4) for q in sa})
            for q in sa:
                mid_v = (q[1] + q[4]) / 2 if ax == 0 else (q[0] + q[3]) / 2
                end = q[ax] < u_sorted[0] + 0.05 or q[ax + 3] > max(w[ax + 3] for w in sa) - 0.05
                if end and (mid_v - kc) * op["ext"] < 0:
                    fails.append(f"[slide] {base}: a fixed pane on the room side")
                    break
        lf = boxes(base + "_Leaf")
        if tp.startswith("D"):
            if not lf:
                fails.append(f"[count] {base}: no leaf")
                continue
            fl = _un_floor(*(((b[0] + b[3]) / 2, kc) if ax == 0 else (kc, (b[1] + b[4]) / 2)))
            if any(abs(q[2] - fl - UN["floor_gap"]) > 1e-4 for q in lf):
                fails.append(f"[leaf] {base}: leaf foot {min(q[2] for q in lf) - fl:.3f} over the floor, spec {UN['floor_gap']}")
            o = objs[base + "_Leaf"].data
            if kind in ("door", "door2"):
                into = UN_SWING.get((op["wall"], op["c"]))
                side = 1 if ((into[1] if ax == 0 else into[0]) > kc) else -1
                if o.get("into") != side:
                    fails.append(f"[swing] {base}: opens out of its room")
                # swing: each leaf about its hinge, 0..90° into the room, quarter disc clear of walls / finishes / devices
                for q in lf:
                    a0, a1 = q[ax], q[ax + 3]
                    pins = ([a0, a1] if kind == "door2" else [a0 if o["hinge"] == "a" else a1])
                    for pin in pins[: (1 if kind != "door2" else 2)]:
                        if kind == "door2":
                            pin = a0 if q is lf[0] and pin == a0 else a1 if q is lf[-1] else pin
                        Lw = a1 - a0
                        other = a1 if abs(pin - a0) < 1e-6 else a0
                        sgn_u = 1 if other > pin else -1
                        blocked = None
                        for deg in range(0, 91, 5):
                            t = math.radians(deg)
                            for rr in (0.2, 0.5, 0.8, 1.0):
                                du, dv = sgn_u * Lw * rr * math.cos(t), side * (UN["depth"] / 2 + Lw * rr * math.sin(t))
                                for zz in (fl + 0.05, fl + 0.40, fl + 1.00, fl + 1.90):
                                    P = [0.0, 0.0, zz]
                                    P[ax], P[1 - ax] = pin + du, kc + dv
                                    if deg > 0 and any(all(w[k] < P[k] < w[k + 3] for k in range(3)) for w in gs.near((*P, *P), 1e-3)):
                                        blocked = (deg, tuple(round(v, 2) for v in P))
                                        break
                                if blocked:
                                    break
                            if blocked:
                                break
                        if blocked:
                            fails.append(f"[swing] {base}: leaf hits something at {blocked[0]}° {blocked[1]}")
                        if kind == "door2":
                            break
                # latch by the room's switch
                for s_ in _coll(C_ELEC).objects:
                    if not (s_.data and s_.data.get("type") == "switch"):
                        continue
                    sb = _el_bounds(s_)
                    su, sv = (sb[ax] + sb[ax + 3]) / 2, (sb[1 - ax] + sb[4 - ax]) / 2
                    if (sv - kc) * side > 0 and abs(sv - kc) < 0.15 and min(abs(su - b[ax]), abs(su - b[ax + 3])) < 0.6 and kind == "door":
                        hinge_u = lf[0][ax] if o["hinge"] == "a" else lf[0][ax + 3]
                        if abs(su - hinge_u) < abs(su - (lf[0][ax + 3] if o["hinge"] == "a" else lf[0][ax])):
                            fails.append(f"[latch] {base}: hinged on the switch side ({s_.name})")
            else:                                                   # sliding: its open position clear
                la, lb, dn = o["slide"]
                Lw = lb - la
                q = lf[0]
                moved = list(q)
                moved[ax], moved[ax + 3] = q[ax] + dn * Lw * 0.98, q[ax + 3] + dn * Lw * 0.98
                s = tuple(moved[k] + 1e-4 for k in range(3)) + tuple(moved[k] - 1e-4 for k in range(3, 6))
                if any((i := _inter(s, w)) and min(i[k + 3] - i[k] for k in range(3)) > 1e-6 for w in gs.near(s)):
                    fails.append(f"[slide] {base}: the leaf slides into something")
    if fails:
        raise AssertionError(f"{len(fails)} failing in units:\n" + "\n".join(fails[:12]))
    return "ST14 ok: " + " · ".join(f"{k} {v}" for k, v in sorted(kinds.items()))
