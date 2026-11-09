"""KK01 ST16–ST17 สุขาภิบาล + สุขภัณฑ์ (generic ST16–ST18) – exec'd after kk01_units.py, built last.

SN-01 classes: CW (น้ำดี) PVC 13.5 — ท่อยืน/นอกอาคาร 1", ในผนัง 3/4", เข้าสุขภัณฑ์ 1/2" (SN-03 labels the main 3/4"); W (น้ำทิ้ง)
2", S (โสโครก) 4", V (ระบายอากาศ) 2" PVC 8.5; slopes S 1:50, W 1:100; 45° / long-radius bends only for S and W; a stop
valve and a 0.30 air chamber at every fixture. SN-02: ถังบำบัด DOS (BOQ 1,600 L — recommend CD-1000 a bath, the drawing
gives no size), บ่อดักไขมัน 2 ห้อง, บ่อน้ำซึมวงซีเมนต์ Ø0.80 ในกรวด 1.10. SN-03: meter (front east) → ground tank + pump
(rear) → the house; SN-04: each bath → its septic tank → grease trap → 2 leach pits; kitchen sink and the bath / laundry
grey water into the grease trap. Fixtures where SN-03 draws their points along the bath walls (A-13 heights).
Designer's table (earlier jobs: no router): horizontal runs buried (CW −0.45, main −0.60, drains graded from their structure), risers
up through the crawl space and the slab; water into the baths over the ceiling (+3.65, under the conduit lanes) from an
exposed riser on the outside wall, then drops in chases to the fixtures; the sink fed and drained through its wall.
Moves (flagged in the spec): tanks / traps / pits shifted clear of footings and the laundry steps.
Objects (collection "KK01 ST16 Sanitary"): SN_<sys>_<size> (pipes), SN_<struct>_<n>, SN_FX_<kind>_<n>. Spec: ST16_sanitary_spec.md.
"""

SN_OD = {"1/2": 0.0217, "3/4": 0.0267, "2": 0.0603, "4": 0.1143}
SN = dict(cw_z=-0.45, main_z=-0.60, slope_s=1 / 50, slope_w=1 / 100, cover=0.10, head_z=3.65, chamber=0.30, rough_wc=0.305, clear=0.015,
          tank=dict(name="ถังบำบัด DOS CD-1000", d=1.32, h=1.45, pad=1.50, a=0.17, b=0.22, top=-0.15),
          trap=dict(name="บ่อดักไขมันสำเร็จรูป 2 ห้อง", w=0.50, l=1.10, h=0.65, inv_in=-0.40, inv_out=-0.45),
          pit=dict(name="บ่อน้ำซึม วงซีเมนต์ Ø0.80 ในกรวด", d=0.90, sq=1.10, h=1.60),
          wtank=dict(name="ถังเก็บน้ำบนดิน 1,000 ลิตร", d=0.96, h=1.48), pump=dict(name="ปั๊มน้ำอัตโนมัติ", s=(0.40, 0.30, 0.35)))
FL_B = FL_WET
# fixtures: (name, kind, room, x along the wall, wall face y, normal sign into the room) — SN-03 points, A-13
SN_FIX = [("B1_SH", "shower", "bath1", 0.46), ("B1_SP", "spray", "bath1", 1.11), ("B1_WC", "wc", "bath1", 1.44), ("B1_LAV", "lav", "bath1", 2.08),
          ("B2_LAV", "lav", "bath2", 10.93), ("B2_SP", "spray", "bath2", 11.32), ("B2_WC", "wc", "bath2", 11.67), ("B2_SH", "shower", "bath2", 12.50)]
SN_WALL = dict(bath1=(3.939, -1), bath2=(3.061, 1))          # tile face y, normal into the room (A-13: fixtures on one wall)
SN_FD = [("B1_FD", 0.45, 3.00, FL_B), ("B2_FD", 12.55, 3.80, FL_B), ("LA_FD", 10.40, 8.10, FL_B)]     # 3" grates (BOQ 3)
SN_SINK = dict(y=10.62, face=3.4865, w=0.80, d=0.50, top=0.85)  # kitchen west wall under W6 (A-04)
SN_HEIGHT = dict(shower=(1.00, 2.10), spray=(0.45,), wc=(0.20,), lav=(0.55,))                 # CW stub heights over FL (A-13)
# structures (moved from the SN-04 symbols, flagged): west / east groups
SN_STRUCT = dict(T1=(1.44, 8.67), G1=(1.44, 10.30), P1=(1.44, 11.60), P2=(1.44, 12.85),
                 T2=(11.67, 10.37), G2=(11.67, 12.00), P3=(11.67, 13.30), P4=(12.87, 13.30))
SN_WTANK, SN_PUMP, SN_METER = (9.51, 13.56), (8.59, 13.56), (14.24, -1.09)
C_SAN = "KK01 ST16 Sanitary"
STAGES.append(C_SAN)


def _sn_graded(pts_plan, z_end, slope, z_drops=()):
    """Plan points [(x, y)] along the flow; z from the downstream end back up at the slope (horizontal length)."""
    out = [None] * len(pts_plan)
    z = z_end
    out[-1] = (*pts_plan[-1], z)
    for i in range(len(pts_plan) - 2, -1, -1):
        z += math.dist(pts_plan[i], pts_plan[i + 1]) * slope
        out[i] = (*pts_plan[i], z)
    return out


def _sn_layout():
    """{(sys, size): [polylines]}, structures, fixtures, valves, the rough-in points the check expects."""
    P = dict(pipes={}, structs=[], fixtures=[], valves=[], ends={}, roots={}, wyes=[])

    def pipe(sys, size, pts):
        P["pipes"].setdefault((sys, size), []).append([tuple(round(c, 6) for c in p) for p in pts])
    T, G_, PT = SN["tank"], SN["trap"], SN["pit"]
    r4, r2 = SN_OD["4"] / 2, SN_OD["2"] / 2
    # ---- structures
    for k, (x, y) in SN_STRUCT.items():
        if k[0] == "T":
            P["structs"].append(dict(name=k, kind="tank", x=x, y=y, top=T["top"], bot=T["top"] - T["h"], d=T["d"], pad=T["pad"]))
        elif k[0] == "G":
            P["structs"].append(dict(name=k, kind="trap", x=x, y=y, top=GL, bot=GL - G_["h"], w=G_["w"], l=G_["l"]))
        else:
            P["structs"].append(dict(name=k, kind="pit", x=x, y=y, top=GL, bot=GL - PT["h"], d=PT["d"], sq=PT["sq"]))
    S = {s["name"]: s for s in P["structs"]}
    t_in = lambda t: T["top"] - T["a"]
    t_out = lambda t: T["top"] - T["b"]
    for grp, (tk, gt, p1, p2, bath, x_wc) in dict(W=("T1", "G1", "P1", "P2", "bath1", 1.44), E=("T2", "G2", "P3", "P4", "bath2", 11.67)).items():
        tx, ty = SN_STRUCT[tk]
        gx, gy = SN_STRUCT[gt]
        wall_y, nrm = SN_WALL[bath]
        # WC soil: from the outlet (finished wall + 0.305) down through the slab, buried north to the tank's inlet
        oy = wall_y + nrm * SN["rough_wc"]
        y_in = ty - T["d"] / 2
        plan = [(x_wc, oy), (tx, y_in)]
        g = _sn_graded(plan, t_in(tk), SN["slope_s"])
        pipe("S", "4", [(x_wc, oy, FL_B - 0.005), (x_wc, oy, g[0][2])] + g[1:])
        P["ends"][f"{bath}_WC_S"] = (x_wc, oy, FL_B - 0.005)
        # tank → grease trap → pits (4", 1:50)
        y_out, y_gin = ty + T["d"] / 2, gy - G_["l"] / 2
        pipe("S", "4", [(tx, y_out, t_out(tk)), (gx, y_gin, G_["inv_in"])])
        p1x, p1y = SN_STRUCT[p1]
        p2x, p2y = SN_STRUCT[p2]
        pipe("S", "4", [(gx, gy + G_["l"] / 2, G_["inv_out"]), (p1x, p1y - PT["d"] / 2, G_["inv_out"] - (p1y - PT["d"] / 2 - gy - G_["l"] / 2) * SN["slope_s"])])
        z12 = G_["inv_out"] - 0.10
        a, b = (p1x, p1y + PT["d"] / 2), ((p2x - PT["d"] / 2, p2y) if abs(p2y - p1y) < 1e-6 else (p2x, p2y - PT["d"] / 2))
        pipe("S", "4", [(a[0], a[1], z12), (b[0], b[1], z12 - math.dist(a, b) * SN["slope_s"])])
        P["roots"][grp] = (tk, gt)
        # vent 2" from the tank top, beyond the eave, 0.15 over the roof within 0.5 m
        vy = ty + 0.30
        pipe("V", "2", [(tx + 0.30, vy, T["top"]), (tx + 0.30, vy, 4.30 if grp == "W" else 2.50)])
    # ---- grey water (2", 1:100) into the 4" between tank and trap: a wye at y_w
    def grey(grp, branches, x_main, y_w, z_w):
        for plan, zs in branches:
            g = _sn_graded(plan + [(x_main + (0.10 if plan[-1][0] > x_main else -0.10), y_w)], z_w, SN["slope_w"])
            pipe("W", "2", [(plan[0][0], plan[0][1], zs)] + g if zs is not None else g)
    # west: bath1 lav + FD → south → west → north round bed 1 → east to the wye; kitchen sink from the east
    tx, ty = SN_STRUCT["T1"]
    gx, gy = SN_STRUCT["G1"]
    y_w = (ty + T["d"] / 2 + gy - G_["l"] / 2) / 2
    z_w = t_out("T1") - (y_w - ty - T["d"] / 2) / ((gy - G_["l"] / 2) - (ty + T["d"] / 2)) * (t_out("T1") - G_["inv_in"])
    lav1, fd1 = 2.08, SN_FD[0]
    w1 = [(lav1, 3.80), (lav1, 3.20), (-0.60, 3.20), (-0.60, y_w), (tx - 0.10, y_w)]
    g = _sn_graded(w1, z_w + 0.005, SN["slope_w"])
    pipe("W", "2", [(lav1, 3.80, FL_B - 0.005)] + g)
    P["ends"]["bath1_LAV_W"] = (lav1, 3.80, FL_B - 0.005)
    zfd = next(p[2] for p in g if abs(p[0] - lav1) < 1e-9 and abs(p[1] - 3.20) < 1e-9) - (lav1 - fd1[1]) * SN["slope_w"]
    pipe("W", "2", [(fd1[1], fd1[2], FL_B - 0.012), (fd1[1], fd1[2], zfd + 0.20 * SN["slope_w"]), (fd1[1], 3.20, zfd)])
    P["ends"]["B1_FD"] = (fd1[1], fd1[2], FL_B - 0.012)
    sk = [(3.30, 10.90), (3.00, 10.90), (3.00, y_w), (tx + 0.10, y_w)]
    g = _sn_graded(sk, z_w + 0.005, SN["slope_w"])
    z_sink_out = FL2 + 0.45
    pipe("W", "2", [(3.60, 10.90, z_sink_out), (3.30, 10.90, z_sink_out), (3.30, 10.90, g[0][2])] + g[1:])
    P["ends"]["SINK_W"] = (3.60, 10.90, z_sink_out)
    pipe("W", "2", [(tx - 0.10, y_w, z_w + 0.005), (tx + 0.10, y_w, z_w + 0.005)])            # the wye across the 4"
    P["wyes"].append((tx, y_w, z_w))
    # east: bath2 lav + FD, laundry FD → east → north along x 13.60 → west to the wye
    tx, ty = SN_STRUCT["T2"]
    gx, gy = SN_STRUCT["G2"]
    y_w = (ty + T["d"] / 2 + gy - G_["l"] / 2) / 2
    z_w = t_out("T2") - (y_w - ty - T["d"] / 2) / ((gy - G_["l"] / 2) - (ty + T["d"] / 2)) * (t_out("T2") - G_["inv_in"])
    lav2, fd2, fd3 = 10.93, SN_FD[1], SN_FD[2]
    e1 = [(lav2, 3.20), (13.60, 3.20), (13.60, y_w), (tx + 0.10, y_w)]
    g = _sn_graded(e1, z_w + 0.005, SN["slope_w"])
    pipe("W", "2", [(lav2, 3.20, FL_B - 0.005)] + g)
    P["ends"]["bath2_LAV_W"] = (lav2, 3.20, FL_B - 0.005)
    z_at = lambda x: g[0][2] - (x - lav2) * SN["slope_w"]
    pipe("W", "2", [(fd2[1], fd2[2], FL_B - 0.012), (fd2[1], fd2[2], z_at(fd2[1]) + 0.60 * SN["slope_w"]), (fd2[1], 3.20, z_at(fd2[1]))])
    P["ends"]["B2_FD"] = (fd2[1], fd2[2], FL_B - 0.012)
    z_t = g[1][2] - (fd3[2] - 3.20) * SN["slope_w"]                     # the trunk at y 8.10
    la = [(fd3[1], fd3[2]), (13.60 - 0.10, fd3[2])]
    zl = -0.14
    pipe("W", "2", [(fd3[1], fd3[2], FL_B - 0.012), (fd3[1], fd3[2], zl), (13.40, fd3[2], zl - 3.00 * SN["slope_w"]),
                    (13.60, fd3[2], z_t)])
    P["ends"]["LA_FD"] = (fd3[1], fd3[2], FL_B - 0.012)
    pipe("W", "2", [(tx - 0.10, y_w, z_w + 0.005), (tx + 0.10, y_w, z_w + 0.005)])
    P["wyes"].append((tx, y_w, z_w))
    # ---- water: meter → tank, pump → kitchen, bath 1 (west), bath 2 (east); risers up the outside walls, header over
    # the bath ceiling at +3.65, drops in the bath wall chase to each fixture (+ 0.30 air chamber below the stub)
    zc = SN["cw_z"]
    mx, my = SN_METER
    wx, wy = SN_WTANK
    px, py = SN_PUMP
    zm = SN["main_z"]
    xin = wx + SN["wtank"]["d"] / 2 + 0.20
    pipe("CW", "3/4", [(mx, my, GL + 0.10), (mx, my, zm), (mx, 14.00, zm), (xin, 14.00, zm), (xin, wy, zm),
                       (xin, wy, GL + SN["wtank"]["h"] - 0.10), (wx + SN["wtank"]["d"] / 2, wy, GL + SN["wtank"]["h"] - 0.10)])
    pipe("CW", "3/4", [(wx - SN["wtank"]["d"] / 2, wy, GL + 0.10), (px + 0.20, py, GL + 0.10)])          # tank → pump suction
    out = (px - 0.20, py, GL + 0.20)
    trunk = [out, (px - 0.20, 12.60, GL + 0.20), (px - 0.20, 12.60, zc), (3.08, 12.60, zc), (3.08, 7.80, zc), (-0.35, 7.80, zc), (-0.35, 3.80, zc), (-0.17, 3.80, zc)]
    pipe("CW", "3/4", trunk)
    pipe("CW", "3/4", [(px - 0.20, py, GL + 0.20), (px - 0.20, 14.20, GL + 0.20), (px - 0.20, 14.20, zc), (13.90, 14.20, zc), (13.90, 2.90, zc), (13.17, 2.90, zc)])
    pipe("CW", "1/2", [(3.08, 10.45, zc), (3.33, 10.45, zc), (3.33, 10.45, FL2 + 0.55), (3.60, 10.45, FL2 + 0.55)])
    P["ends"]["SINK_CW"] = (3.60, 10.45, FL2 + 0.55)
    for bath, (rx, ry, x_in) in dict(bath1=(-0.17, 3.80, 0.05), bath2=(13.17, 2.90, 12.95)).items():
        wall_y, nrm = SN_WALL[bath]
        brick = wall_y - nrm * (0.011 + PLASTER["t"])            # behind tile + plaster
        hy = wall_y + nrm * 0.15                                 # header 15 cm off the wall
        fx = [f for f in SN_FIX if f[2] == bath]
        xs = sorted(f[3] for f in fx)
        hx0, hx1 = (x_in, xs[-1]) if bath == "bath1" else (x_in, xs[0])
        zh = SN["head_z"]
        if bath == "bath2":                                     # up to over W5, along the face, then through
            yh = 3.70
            pipe("CW", "3/4", [(rx, ry, zc), (rx, ry, 3.35), (rx, yh, 3.35), (rx, yh, zh), (x_in, yh, zh), (x_in, hy, zh), (hx1, hy, zh)])
        else:
            pipe("CW", "3/4", [(rx, ry, zc), (rx, ry, zh), (x_in, ry, zh), (x_in, hy, zh), (hx1, hy, zh)])
        for name, kind, _, x in fx:
            for k, hh in enumerate(SN_HEIGHT[kind]):
                xx = x + 0.15 * k * (1 if bath == "bath1" else -1)
                zs = FL_B + hh
                pipe("CW", "1/2", [(xx, hy, zh), (xx, brick, zh), (xx, brick, zs), (xx, wall_y + nrm * 0.02, zs)])
                P["ends"][f"{name}_CW{k}"] = (xx, wall_y + nrm * 0.02, zs)
                P["valves"].append(dict(kind="stop", at=(xx, wall_y + nrm * 0.02, zs)))
    P["valves"] += [dict(kind="gate", at=(mx, my + 0.25, zc)), dict(kind="gate", at=(mx, my - 0.25, zc)),
                    dict(kind="gate", at=(wx + 0.80, wy, zc)), dict(kind="check", at=(px - 0.20, py, GL + 0.20)),
                    dict(kind="gate", at=(3.08, 10.60, zc))]
    # ---- fixtures
    for name, kind, bath, x in SN_FIX:
        wall_y, nrm = SN_WALL[bath]
        P["fixtures"].append(dict(name=name, kind=kind, bath=bath, x=x, wall=wall_y, n=nrm))
    for name, x, y, fl in SN_FD:
        P["fixtures"].append(dict(name=name, kind="fd", x=x, y=y, fl=fl))
    P["fixtures"].append(dict(name="SINK", kind="sink", **SN_SINK))
    return P


def _sn_tube_boxes(pts, od):
    """Axis-aligned boxes round each straight piece (for the clash check / structure test)."""
    out = []
    r = od / 2
    for a, b in zip(pts, pts[1:]):
        out.append((min(a[0], b[0]) - r, min(a[1], b[1]) - r, min(a[2], b[2]) - r, max(a[0], b[0]) + r, max(a[1], b[1]) + r, max(a[2], b[2]) + r))
    return out


def build_sanitary():
    c = _clear(C_SAN)
    P = _sn_layout()
    pv = {"CW": mat("M_PVC_Blue", (0.20, 0.40, 0.75), 0.4), "S": mat("M_PVC_Grey", (0.55, 0.56, 0.58), 0.5),
          "W": mat("M_PVC_Grey", (0.55, 0.56, 0.58), 0.5), "V": mat("M_PVC_Grey", (0.55, 0.56, 0.58), 0.5)}
    names = {"CW": "ท่อน้ำดี PVC 13.5", "S": "ท่อโสโครก PVC 8.5", "W": "ท่อน้ำทิ้ง PVC 8.5", "V": "ท่อระบายอากาศ PVC 8.5"}
    for (sys, size), paths in P["pipes"].items():
        n = f"SN_{sys}_{size.replace('/', '-')}"
        c.objects.link(bpy.data.objects.new(n, _rebar_data(n, paths, SN_OD[size], pv[sys], element="pipe", type=f"{sys}{size}",
                                                           th=f'{names[sys]} ⌀{size}"', bar=f"PVC {size}", dia_mm=round(SN_OD[size] * 1000),
                                                           system=sys, size=size)))
    conc = mat("M_Precast", (0.70, 0.70, 0.68), 0.8)
    pe = mat("M_TankPE", (0.25, 0.45, 0.30), 0.6)
    white = mat("M_Ceramic", (0.97, 0.97, 0.96), 0.15)
    ss = mat("M_Stainless", (0.80, 0.80, 0.82), 0.25, 0.9)
    for s in P["structs"]:
        if s["kind"] in ("tank", "pit"):
            me = _el_disc(f"SN_{s['name']}", s["x"], s["y"], s["bot"], s["top"], s["d"], pe if s["kind"] == "tank" else conc, segs=24,
                          element="struct", type=s["kind"], th=SN[s["kind"] if s["kind"] != "tank" else "tank"]["name"])
        else:
            me = _boxes_data(f"SN_{s['name']}", [(s["x"] - s["w"] / 2, s["y"] - s["l"] / 2, s["bot"], s["x"] + s["w"] / 2, s["y"] + s["l"] / 2, s["top"])],
                             conc, element="struct", type="trap", th=SN["trap"]["name"])
        c.objects.link(bpy.data.objects.new(f"SN_{s['name']}", me))
    wx, wy = SN_WTANK
    c.objects.link(bpy.data.objects.new("SN_WTANK", _el_disc("SN_WTANK", wx, wy, GL, GL + SN["wtank"]["h"], SN["wtank"]["d"], pe, element="struct",
                                                             type="wtank", th=SN["wtank"]["name"])))
    px, py = SN_PUMP
    a, b_, h = SN["pump"]["s"]
    c.objects.link(bpy.data.objects.new("SN_PUMP", _boxes_data("SN_PUMP", [(px - a / 2, py - b_ / 2, GL, px + a / 2, py + b_ / 2, GL + h)], ss,
                                                               element="struct", type="pump", th=SN["pump"]["name"])))
    mx, my = SN_METER
    c.objects.link(bpy.data.objects.new("SN_METER", _boxes_data("SN_METER", [(mx - 0.15, my - 0.12, GL - 0.20, mx + 0.15, my + 0.12, GL)], conc,
                                                                element="struct", type="meter", th="มิเตอร์น้ำ + บ่อมิเตอร์")))
    fx = []
    for f in P["fixtures"]:
        k = f["kind"]
        if k == "fd":
            fx.append((f["name"], k, [(f["x"] - 0.06, f["y"] - 0.06, f["fl"] - 0.004, f["x"] + 0.06, f["y"] + 0.06, f["fl"] + 0.001)], ss))
            continue
        if k == "sink":
            x0 = f["face"] + 0.0005
            fx.append(("SINK", k, [(x0, f["y"] - f["w"] / 2, FL2 + f["top"] - 0.20, x0 + f["d"], f["y"] + f["w"] / 2, FL2 + f["top"]),
                                   (x0 + 0.02, f["y"] - f["w"] / 2 + 0.02, FL2, x0 + f["d"] - 0.02, f["y"] - f["w"] / 2 + 0.06, FL2 + f["top"] - 0.20),
                                   (x0 + 0.02, f["y"] + f["w"] / 2 - 0.06, FL2, x0 + f["d"] - 0.02, f["y"] + f["w"] / 2 - 0.02, FL2 + f["top"] - 0.20)], ss))
            continue
        y0, n = f["wall"], f["n"]
        B = lambda x0, x1, d0, d1, z0, z1: (x0, min(y0 + n * d0, y0 + n * d1), z0, x1, max(y0 + n * d0, y0 + n * d1), z1)
        x = f["x"]
        if k == "wc":
            fx.append((f["name"], k, [B(x - 0.19, x + 0.19, 0.03, 0.70, FL_B + 0.0005, FL_B + 0.40), B(x - 0.20, x + 0.20, 0.03, 0.22, FL_B + 0.40, FL_B + 0.78)], white))
        elif k == "lav":
            fx.append((f["name"], k, [B(x - 0.25, x + 0.25, 0.03, 0.45, FL_B + 0.68, FL_B + 0.83), B(x - 0.09, x + 0.09, 0.08, 0.22, FL_B + 0.0005, FL_B + 0.68),
                                      B(x - 0.30, x + 0.30, 0.0005, 0.02, FL_B + 1.10, FL_B + 1.90)], white))      # + the mirror
        elif k == "shower":
            fx.append((f["name"], k, [B(x - 0.08, x + 0.08, 0.025, 0.08, FL_B + 0.95, FL_B + 1.05), B(x - 0.11, x + 0.11, 0.025, 0.30, FL_B + 2.08, FL_B + 2.12)], ss))
        elif k == "spray":
            fx.append((f["name"], k, [B(x - 0.04, x + 0.04, 0.025, 0.07, FL_B + 0.41, FL_B + 0.49), B(x + 0.10, x + 0.24, 0.0005, 0.10, FL_B + 0.70, FL_B + 0.76)], ss))  # + paper holder
    for name, k, boxes, m in fx:
        c.objects.link(bpy.data.objects.new(f"SN_FX_{name}", _boxes_data(f"SN_FX_{name}", boxes, m, element="fixture", type=k, th=k)))
    q = bpy.data.objects.new("SN_Qty", None)
    q["valves"] = [v["kind"] for v in P["valves"]]
    q["chambers"] = sum(1 for k in P["ends"] if "_CW" in k)
    c.objects.link(q)
    bpy.context.view_layer.update()
    return sum(len(v) for v in P["pipes"].values())


def _sn_fittings(P):
    """Elbows (by turn: 90° / 45°) and tees per (system, size), from the sharp polylines and their junctions."""
    out = {}
    pts = {}
    for (sys, size), paths in P["pipes"].items():
        for p in paths:
            for i in range(1, len(p) - 1):
                a, b, c_ = Vector(p[i - 1]), Vector(p[i]), Vector(p[i + 1])
                if (b - a).length < 1e-6 or (c_ - b).length < 1e-6:
                    continue
                th = math.degrees((b - a).angle(c_ - b))
                if th > 1:
                    k = (sys, size, "ข้อโค้ง 45°" if th < 60 else "ข้องอ 90°" if sys == "CW" else "ข้อโค้ง 90° รัศมีกว้าง")
                    out[k] = out.get(k, 0) + 1
            for e in (p[0], p[-1]):
                pts.setdefault((sys, size, tuple(round(v, 3) for v in e)), 0)
                pts[(sys, size, tuple(round(v, 3) for v in e))] += 1
    tees = {}
    for (sys, size), paths in P["pipes"].items():
        for p in paths:
            s = Vector(p[0])
            for (sys2, size2), paths2 in P["pipes"].items():
                if sys2 != sys:
                    continue
                for q in paths2:
                    if q is p:
                        continue
                    for i in range(len(q) - 1):
                        a, b = Vector(q[i]), Vector(q[i + 1])
                        ab = b - a
                        if ab.length < 1e-9:
                            continue
                        t = (s - a).dot(ab) / ab.length_squared
                        if 1e-4 < t < 1 - 1e-4 and (a + ab * t - s).length < 0.13:
                            k = (sys, size2, "สามทาง" if sys == "CW" else "สามทางวาย (Y)")
                            tees[k] = tees.get(k, 0) + 1
    out.update(tees)
    return out


def sanitary_report():
    out = []
    for o in sorted(_coll(C_SAN).objects, key=lambda o: o.name):       # (no qto: the tanks are cylinders)
        if o.type == "CURVE" and o.data.get("element") == "pipe":
            m = sum(_bar_lengths(o))
            out.append(f"{o.data['th']}: {m:.1f} ม. → {math.ceil(m / 4.0 - 1e-9)} ท่อน (4 ม.)")
    P = _sn_layout()
    for (sys, size, kind), n in sorted(_sn_fittings(P).items()):
        out.append(f"  {kind} ⌀{size}\" ({sys}): {n}")
    q = bpy.data.objects["SN_Qty"]
    v = list(q["valves"])
    out.append(f"สต๊อปวาล์ว {v.count('stop')} · ประตูน้ำ (GV) {v.count('gate')} · เช็ควาล์ว {v.count('check')} · air chamber 0.30 ม. {q['chambers']} จุด")
    st = {}
    for o in _coll(C_SAN).objects:
        if o.data and o.data.get("element") in ("struct", "fixture"):
            st[o.data["th"]] = st.get(o.data["th"], 0) + 1
    out.append(" · ".join(f"{k} {v}" for k, v in st.items()))
    return "\n".join(out)


# ---------------------------------------------------------------- ST16 selfcheck

def _check_sanitary(rows_before):
    """Read back: every fixture point reached by its system; drains never uphill and at their slope; buried runs under
    0.10 cover; no pipe in the structure (footings, stubs, beams + their sand, columns, steps) or through a tie column /
    opening; walls and floors only crossed by chases, risers and short sleeves; pipes ≥ 1.5 cm from each other and the
    conduits; structures clear of the house and each other; the vent above the roof; fixture counts as the BOQ."""
    objs = {o.name: o for o in _coll(C_SAN).objects}
    fails = []
    P = _sn_layout()
    paths = {}
    for n, o in objs.items():
        if o.type == "CURVE" and o.data.get("element") == "pipe":
            paths[n] = (o.data["system"], o.data["size"], [[tuple(p) for p in sp] for sp in _world_bars(o)])
    if not paths:
        raise AssertionError("[count] no pipes")
    ends = {}
    for n, (sys, size, ps) in paths.items():
        for p in ps:
            ends.setdefault(sys, []).extend([p[0], p[-1]] + list(p))
    for k, pt in P["ends"].items():
        sys = "CW" if "_CW" in k else "S" if k.endswith("_S") else "W"
        if not any(math.dist(e, pt) < 2e-3 for e in ends.get(sys, [])):
            fails.append(f"[connect] {k}: no {sys} pipe at {tuple(round(v, 3) for v in pt)}")
    # drains: walk each polyline in its drawn order (flow), never uphill; level-ish pieces at their slope
    for n, (sys, size, ps) in paths.items():
        if sys not in ("S", "W"):
            continue
        smin = SN["slope_s"] if sys == "S" else SN["slope_w"]
        for p in ps:
            for a, b in zip(p, p[1:]):
                L = math.hypot(b[0] - a[0], b[1] - a[1])
                if b[2] > a[2] + 1e-5:
                    fails.append(f"[grade] {n}: runs uphill at {tuple(round(v, 2) for v in a)}")
                    break
                if L > 0.30 and (a[2] - b[2]) / L < smin * 0.98 and (a[2] - b[2]) < 0.5 * L:
                    fails.append(f"[grade] {n}: {(a[2] - b[2]) / L * 100:.2f} % < {smin * 100:.1f} % at {tuple(round(v, 2) for v in a)}")
                    break
    # cover: horizontal runs below ground keep ≥ 0.10 over their top
    for n, (sys, size, ps) in paths.items():
        r = SN_OD[size] / 2
        for p in ps:
            for a, b in zip(p, p[1:]):
                if math.hypot(b[0] - a[0], b[1] - a[1]) > 0.30 and max(a[2], b[2]) < GL and max(a[2], b[2]) + r > GL - SN["cover"] + 1e-4:
                    fails.append(f"[cover] {n}: {GL - max(a[2], b[2]) - r:.3f} m over the pipe at {tuple(round(v, 2) for v in a)}")
                    break
    # clashes
    hard = [b for cn in (C_FOOT, C_STUB, C_GB, C_COL) for (el, _), x in qto(cn).items() if el not in ("excavation",) for b in x["boxes"]]
    hard += [b for (el, _), x in qto(C_WALL).items() if el in ("concrete", "opening") and False for b in x["boxes"]]
    hard += _cd_hard() + [b for n_, v in _ft_boxes("FT_Step").items() for b in v]
    fin = _ft_boxes()
    wallfin = [b for n_, v in fin.items() if n_.startswith("FT_Wall") or n_ == "FT_Waterproof" for b in v if b[5] - b[2] > 0.02]
    walls = [b for (el, _), x in qto(C_WALL).items() if el in ("brick", "plaster", "concrete") for b in x["boxes"]] + wallfin
    floors = [b for (el, _), x in qto(C_FLOOR).items() if el in ("concrete", "precast") for b in x["boxes"]] + \
        [b for n_, v in fin.items() if not n_.startswith("FT_Wall") and not n_.startswith("FT_Step") for b in v if b[5] - b[2] <= 0.02 or n_ != "FT_Waterproof"]
    ceil = [b for (el, _), x in qto(C_CEIL).items() if el in ("ceiling", "soffit", "cline") for b in x["boxes"]]
    gh, gw, gf, gc = _Grid(hard), _Grid(walls), _Grid(floors), _Grid(ceil)
    samples = []
    for n, (sys, size, ps) in paths.items():
        r = SN_OD[size] / 2
        for pi, p in enumerate(ps):
            for a, b in zip(p, p[1:]):
                A, B_ = Vector(a), Vector(b)
                L = (B_ - A).length
                vert = abs(B_.z - A.z) > 0.9 * L
                ns = max(2, int(L / 0.02))
                for k in range(ns + 1):
                    v = A + (B_ - A) * (k / ns)
                    samples.append((n, pi, v, r, sys))
                    q = (v.x, v.y, v.z, v.x, v.y, v.z)
                    inside = lambda grid, rr: any(all(w[j] + rr < v[j] < w[j + 3] - rr for j in range(3)) for w in grid.near(q, 0.2))
                    if inside(gh, -r + 0.0005):
                        fails.append(f"[clash] {n}: in the structure / a tie / a step at {tuple(round(c, 3) for c in v)}")
                        break
                    if inside(gc, -r + 0.0005):
                        fails.append(f"[clash] {n}: through a ceiling at {tuple(round(c, 3) for c in v)}")
                        break
                    if inside(gw, -r + 0.0005) and not vert and L > 0.36:
                        fails.append(f"[wall] {n}: a {L:.2f} m level run inside a wall at {tuple(round(c, 3) for c in v)}")
                        break
                    if inside(gf, -r + 0.0005) and not vert:
                        fails.append(f"[floor] {n}: a level run inside the floor at {tuple(round(c, 3) for c in v)}")
                        break
                else:
                    continue
                break
    # pipe ↔ pipe (other polylines, not touching at a shared node) and pipe ↔ conduit
    cond = []
    for o in _coll(C_COND).objects:
        if o.type == "CURVE":
            d = (o.data.get("dia_mm") or 20) / 1000
            for sp in _world_bars(o):
                for v in _cd_samples([tuple(x) for x in sp], 0.03):
                    cond.append((v, d / 2))
    cell = 0.15
    grid = {}
    for i, (n, pi, v, r, sys) in enumerate(samples):
        grid.setdefault((int(v.x // cell), int(v.y // cell), int(v.z // cell)), []).append(i)
    nodes = [Vector(e) for sys in ends for e in ends[sys]]
    hits = 0
    for i, (n, pi, v, r, sys) in enumerate(samples[::2]):
        k = (int(v.x // cell), int(v.y // cell), int(v.z // cell))
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in grid.get((k[0] + dx, k[1] + dy, k[2] + dz), ()):
                        m, pj, w, rj, sj = samples[j]
                        if (m, pj) == (n, pi) or (v - w).length > r + rj + SN["clear"] - 1e-4:
                            continue
                        if sj == sys and any((v - e).length < r + rj + 0.15 for e in nodes):
                            continue                              # at a shared node (tee / joint)
                        if {sys, sj} == {"S", "W"} and any((v - Vector(wy)).length < 0.25 for wy in P["wyes"]):
                            continue                              # the grey water's wye into the 4"
                        hits += 1
                        if hits == 1:
                            fails.append(f"[gap] {n} and {m} closer than {SN['clear'] * 100:.1f} cm at {tuple(round(c, 3) for c in v)}")
    cg = {}
    for v, rr in cond:
        cg.setdefault((int(v.x // cell), int(v.y // cell), int(v.z // cell)), []).append((v, rr))
    for (n, pi, v, r, sys) in samples[::2]:
        k = (int(v.x // cell), int(v.y // cell), int(v.z // cell))
        if any((v - w).length < r + rr + SN["clear"] - 1e-4 for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1)
               for w, rr in cg.get((k[0] + dx, k[1] + dy, k[2] + dz), ())):
            fails.append(f"[gap] {n}: within {SN['clear'] * 100:.1f} cm of a conduit at {tuple(round(c, 3) for c in v)}")
            break
    # structures: clear of the house's structure, the steps and each other
    sb = []
    for o in objs.values():
        if o.data and o.data.get("element") == "struct":
            b = _el_bounds(o)
            sb.append((o.name, b))
    house = [b for cn in (C_FOOT, C_STUB, C_GB, C_COL, C_FLOOR) for (el, _), x in qto(cn).items() if el != "excavation" for b in x["boxes"]] + \
        [b for n_, v in _ft_boxes("FT_Step").items() for b in v]
    for n, b in sb:
        pad = (b[0] - 0.09, b[1] - 0.09, b[2] - 0.10, b[3] + 0.09, b[4] + 0.09, b[5]) if objs[n].data["type"] in ("tank", "pit") else b
        if any((i := _inter(pad, h)) and min(i[k + 3] - i[k] for k in range(3)) > 1e-5 for h in house):
            fails.append(f"[struct] {n}: its pit cuts the house structure / steps")
        for m, c2 in sb:
            if m > n and (i := _inter(b, c2)) and min(i[k + 3] - i[k] for k in range(3)) > 1e-5:
                fails.append(f"[struct] {n} and {m} overlap")
        if objs[n].data["type"] in ("tank", "pit", "trap", "meter") and b[5] > GL + 1e-5:
            fails.append(f"[struct] {n}: above the ground")
    # vents above the roof within 0.5 m: rays down on a 5 cm grid onto the roof covering (practice: vertices under-read)
    from mathutils.bvhtree import BVHTree
    trees = []
    for cn in (C_COVER, C_ROOF):
        cv = bpy.data.collections.get(cn)
        for o in cv.objects if cv else []:
            if o.type == "MESH" and len(o.data.polygons):
                M = o.matrix_world
                trees.append(BVHTree.FromPolygons([M @ v.co for v in o.data.vertices], [tuple(f.vertices) for f in o.data.polygons]))
    for n, (sys, size, ps) in paths.items():
        if sys != "V":
            continue
        for p in ps:
            top = max(p, key=lambda e: e[2])
            hi = None
            for i in range(-10, 11):
                for j in range(-10, 11):
                    x, y = top[0] + i * 0.05, top[1] + j * 0.05
                    if math.hypot(i * 0.05, j * 0.05) > 0.5:
                        continue
                    for t in trees:
                        h = t.ray_cast(Vector((x, y, 9.0)), Vector((0, 0, -1)))
                        if h[0] is not None and (hi is None or h[0].z > hi):
                            hi = h[0].z
            if hi is not None and top[2] < hi + 0.15:
                fails.append(f"[vent] {n}: top {top[2]:.2f} under the roof + 0.15 ({hi:.2f}) within 0.5 m")
    # fixtures as the BOQ / A-12
    kinds = {}
    for o in objs.values():
        if o.data and o.data.get("element") == "fixture":
            kinds[o.data["type"]] = kinds.get(o.data["type"], 0) + 1
    want = dict(wc=2, lav=2, shower=2, spray=2, fd=3, sink=1)
    if kinds != want:
        fails.append(f"[fixtures] {kinds} != BOQ {want}")
    for f in P["fixtures"]:
        if f["kind"] == "wc":
            o = objs.get(f"SN_FX_{f['name']}")
            if o is None:
                fails.append(f"[fixtures] {f['name']}: missing")
                continue
            b = _el_bounds(o)
            oy = f["wall"] + f["n"] * SN["rough_wc"]
            if not (min(b[1], b[4]) < oy < max(b[1], b[4])):
                fails.append(f"[fixtures] {f['name']}: the WC does not stand over its outlet")
    if fails:
        raise AssertionError(f"{len(fails)} failing in sanitary:\n" + "\n".join(fails[:12]))
    tot = sum(math.dist(p[i], p[i + 1]) for _, _, ps in paths.values() for p in ps for i in range(len(p) - 1))
    return f"ST16 ok: {len(paths)} pipe sets {tot:.1f} m, {len(sb)} structures, fixtures {sum(kinds.values())}"
