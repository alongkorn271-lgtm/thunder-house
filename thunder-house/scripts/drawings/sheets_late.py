# -*- coding: utf-8 -*-
# Sheets ST-07 … ST-18. Exec'd from make_sheets.py (shares its namespace: D, parts, MESH, LINES, helpers).
import math
from dwg_lib import hull

for _p in parts:
    if _p["g"] == 9:
        _p["mc"] = "paint"
WALLS = lambda p: p["g"] in (4, 5) and not p.get("rb") and p["e"] in ("brick", "concrete") and p["mc"] != "steel"


def base_plan(sh, title, sub, plane=None, crop=PLAN_CROP):
    v = sh.view("plan", 125, crop, (36, 214), plane=plane, title=title, sub=sub, tdy=17)
    grids(v, ext=(5, 5))
    grid_dims(v, below=8, left=8)
    return v


def overlay(sh, v, plane=None):
    """second view on the same paper window (e.g. walls cut at +1.50 over a ceiling plan)"""
    return sh.view(v.kind, v.s, v.crop, v.at, plane=plane)


def draw_meshes(v, items, fill, stroke="#2b2b2b", sw=0.12, op=1.0):
    out = []
    for m in items:
        uv = [v.uv(q) for q in m["v"]]
        poly = hull(uv)
        if len(poly) < 3:
            continue
        depth = max(v.near(q) for q in m["v"])
        o = f' fill-opacity="{op}"' if op < 1 else ""
        out.append((depth, v._poly(poly, fill(m), stroke, sw, o)))
    out.sort(key=lambda t: t[0])
    v.out += [t[1] for t in out]


def draw_lines(v, items, color, sw=0.35, dash=None):
    for m in items:
        c = color(m) if callable(color) else color
        d = dash(m) if callable(dash) else dash
        da = f' stroke-dasharray="{d}"' if d else ""
        for poly in m["polys"]:
            pts = " ".join(f"{f(a)},{f(b)}" for a, b in (v.P(q) for q in poly))
            v.out.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-width="{sw}" stroke-linejoin="round"{da}/>')


def obj_bbox(name):
    bs = [bbox(p) for p in parts if p["obj"] == name]
    if not bs:
        m = next((m for m in MESH if m["n"] == name), None)
        if not m:
            return None
        xs, ys, zs = zip(*m["v"])
        return [min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)]
    return [min(b[k] for b in bs) for k in range(3)] + [max(b[k + 3] for b in bs) for k in range(3)]


def center(b):
    return [(b[k] + b[k + 3]) / 2 for k in range(3)]


def elevation(sh, at, scale, pred, meshes=(), title="รูปด้านหน้า  FRONT ELEVATION", sub="", crop=(-1300, 14300, -300, 6600), tdy=9):
    v = sh.view("front", scale, crop, at, title=title, sub=sub, tdy=tdy)
    v.draw_parts(pred)
    draw_meshes(v, meshes, lambda m: TINTS.get(m["e"], "#e4e6e8"))
    v.uvline((crop[0], 0), (crop[1], 0), sw=0.3)
    for z, lab in ((0, "±0.00 GL"), (800, "+0.80"), (4175, "+4.175")):
        v.text_uv(crop[1] - 100, z + 60, lab, 1.7, "end", color="#444")
    return v


TINTS = {"steel": "#d8dadc", "tile_bed": "#a9b1ba", "struct": "#e7eef2", "elec": "#f2f2f2", "": "#f2f2f2"}


def legend_at(sh, x, y, items, cols=2, colw=40):
    for i, (fill, lab) in enumerate(items):
        xx, yy = x + (i % cols) * colw, y + (i // cols) * 4.4
        sh.add(f'<rect x="{xx}" y="{yy - 2.6}" width="6" height="3.2" fill="{fill}" stroke="#111" stroke-width="0.15"/>')
        sh.add(text(xx + 8, yy, lab, 1.95, "start"))


def late_sheet(no, stage, sheet_title, title, desc, highs, scale_note, plan_fn, right_fn, rep=None, cap="", img_detail=True):
    sh = Sheet(no, sheet_title, scale_note, TOTAL)
    img(sh, f"{stage}_stage", 178, 14, 168, 100)
    sh.add(text(180, 118, "ภาพ 3 มิติ: งานขั้นนี้แสดงสีจริง · งานก่อนหน้าแสดงเป็นสีขาว", 1.9, "start", 400, "#555"))
    panel(sh, 14, 14, 160, 58, no, title, desc, highs)
    plan_fn(sh)
    if img_detail:
        img(sh, f"{stage}_detail", 292, 124, 54, 39)
        sh.add(text(319, 166.5, cap, 1.8, "middle", 400, "#555"))
    right_fn(sh)
    qty_table(sh, 16, 248, 158, rep or stage, 99, maxh=36)
    SH.append(sh)
    return sh


# ---------------- ST-07 roof frame ----------------
RF_COL = [("RF_plate", "#5bb8a8", "อะเส / ขื่อ 2[]125"), ("RF_ridge", "#e8c14a", "อกไก่ 2[]125"), ("RF_hip", "#f08a6a", "ตะเข้สัน 2[]125"),
          ("RF_valley", "#c0563f", "ตะเข้ราง 2[]125"), ("RF_post", "#8a8f96", "ดั้ง 2[]125"), ("RF_rafter", "#6fb7e0", "จันทัน C100"),
          ("RF_batten", "#c7b6e3", "ระแนง 1\"×1\""), ("RF_support", "#3f8f80", "รับจันทันเพิง 2[]125"),
          ("RF_lean_rafter", "#9bd0ee", "จันทันเพิง C100"), ("RF_purlin", "#ab95d6", "แปเพิง C75")]


def rf_fill(m):
    for k, c, _ in RF_COL:
        if m["n"].startswith(k + "_") or m["n"] == k:
            return c
    return "#ddd"


def p07(sh):
    v = base_plan(sh, "ผังโครงหลังคา  ROOF FRAMING PLAN", "มองจากบน · 1:125")
    v.draw_parts(lambda p: p["g"] == 4 and p["e"] == "concrete" and not p.get("rb"), color="#999")
    order = ["RF_plate", "RF_support", "RF_ridge", "RF_post", "RF_hip", "RF_valley", "RF_rafter", "RF_lean_rafter", "RF_purlin", "RF_batten"]
    ms = sorted([m for m in MESH if m["g"] == 6], key=lambda m: next((i for i, k in enumerate(order) if m["n"].startswith(k)), 99))
    for m in ms:   # draw in a fixed layer order (battens on top) rather than by depth
        poly = hull([v.uv(q) for q in m["v"]])
        if len(poly) >= 3:
            v.out.append(v._poly(poly, rf_fill(m), "#222", 0.08))


def r07(sh):
    legend_at(sh, 182, 176, [(c, l) for _, c, l in RF_COL], cols=2, colw=46)
    v = elevation(sh, (190, 270), 125, lambda p: p["g"] == 4 and p["e"] == "concrete" and not p.get("rb"),
                  [m for m in MESH if m["g"] == 6], title="รูปด้านโครงหลังคา  FRAME ELEVATION", sub="มองจากด้านหน้า · 1:125",
                  crop=(-1300, 14300, 500, 6600))


late_sheet("ST-07", "ST07", "โครงหลังคาเหล็ก", "โครงหลังคาเหล็ก",
           ["หลังคาปั้นหยา 30° รวม 3 หลัง (บ้านหลัก + มุขซ้าย + มุขขวา) โครงเหล็กรูปพรรณทั้งหมด ไม่มีคานหลังคา คสล.",
            "เพิงหลังและกันสาดหน้าประตูเป็นเมทัลชีทบนแป C75"],
           ["อะเส/ขื่อ/อกไก่/ตะเข้/ดั้ง 2[]125×50×20×2.3 รวม 175.0 ม. → 60 เส้น",
            "จันทัน C100 208.3 ม. · ระแนง 1\"×1\" 456.2 ม. · แป C75 60.8 ม.",
            "อกไก่ หลัก +6.30 / มุขซ้าย +5.87 / มุขขวา +5.44 · ชายคา +3.85"],
           "1:125", p07, r07, cap="ตะเข้ราง + ตะเข้สันที่มุขหน้า")


# ---------------- ST-08 roof cover ----------------
def slope_arrows(v, meshes):
    for m in meshes:
        V, F = m["v"], m["f"]
        a, b, c = (V[F[0]], V[F[1]], V[F[2]]) if len(F) >= 3 else (None, None, None)
        if a is None:
            continue
        u = [b[k] - a[k] for k in range(3)]; w = [c[k] - a[k] for k in range(3)]
        n = [u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0]]
        if n[2] < 0:
            n = [-x for x in n]
        h = math.hypot(n[0], n[1])
        if h < 1e-6:
            continue
        dx, dy = n[0] / h, n[1] / h
        xs, ys, zs = zip(*V)
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        A, B = v.pp(cx - dx * 700, cy - dy * 700), v.pp(cx + dx * 700, cy + dy * 700)
        v.ann.append(f'<line x1="{f(A[0])}" y1="{f(A[1])}" x2="{f(B[0])}" y2="{f(B[1])}" stroke="#1d3a5a" stroke-width="0.25" marker-end="url(#arr)"/>')
        v.ann.append(text((A[0] + B[0]) / 2 + 1.5, (A[1] + B[1]) / 2 - 1.2, "30°", 1.8, "start", 600, "#1d3a5a"))


def p08(sh):
    v = base_plan(sh, "ผังหลังคา  ROOF PLAN", "มองจากบน · ลูกศรชี้ทางน้ำไหล · 1:125")
    v.draw_parts(lambda p: p["g"] == 7)
    tiles = [m for m in MESH if m["g"] == 7]
    draw_meshes(v, tiles, lambda m: "#b9c0c8", sw=0.16)
    slope_arrows(v, tiles)


def r08(sh):
    legend_at(sh, 182, 176, [("#b9c0c8", "กระเบื้อง CPAC โมเนีย 30°"), ("#d8dadc", "เมทัลชีท + PU (เพิง / กันสาด)"), ("#ead9bd", "เชิงชาย SCG 2in1")], cols=1)
    elevation(sh, (190, 270), 125, lambda p: p["g"] in (4, 5, 7, 13) and not p.get("rb") and p["e"] not in ("plaster",),
              [m for m in MESH if m["g"] == 7], sub="หลังมุงหลังคา · 1:125")


late_sheet("ST-08", "ST08", "มุงหลังคา + รูปด้านหน้า", "มุงหลังคา",
           ["กระเบื้อง CPAC โมเนีย 33×42 ซม. บนระแนง พื้นที่ลาด 161.66 ตร.ม. ครอบสัน/ครอบตะเข้นับจากความยาวจริง",
            "เพิงหลังและกันสาดหน้าประตูเป็นเมทัลชีท 0.3 มม. + PU 1\""],
           ["กระเบื้อง 1,790 แผ่น (เผื่อ 5 %) · แผ่นรองสะท้อนความร้อน 161.66 ตร.ม.",
            "ครอบสันโค้ง 150 แผ่น · ครอบสามทาง 6 · หางมน 6 · รางตะเข้ 9.55 ม.",
            "เชิงชาย 2in1 50.87 ม. · เมทัลชีท 48.05 ตร.ม."],
           "1:125", p08, r08, cap="หลังคาด้านหลัง + เพิง")


# ---------------- ST-09 ceilings ----------------
CE_FILL = {"ฝ้ายิปซัมบอร์ดธรรมดา 9 มม.": "#ffffff", "ฝ้ายิปซัมบอร์ดกันชื้น 9 มม.": "#dbe9f2", "SCG Smartboard ระบายอากาศ 4 มม.": "#ecdcc0"}
CE_MARK = {"ฝ้ายิปซัมบอร์ดธรรมดา 9 มม.": "CL1", "ฝ้ายิปซัมบอร์ดกันชื้น 9 มม.": "CL2", "SCG Smartboard ระบายอากาศ 4 มม.": "CL3"}


def p09(sh):
    v = base_plan(sh, "ผังฝ้าเพดาน  REFLECTED CEILING PLAN", "มองขึ้นจากพื้น (กลับด้านเหมือนมองจากบน) · 1:125")
    boards = lambda p: p["g"] == 8 and p["e"] in ("ceiling", "soffit")
    for tname, fill in CE_FILL.items():
        D.TINT["ce_" + CE_MARK[tname]] = fill
        D.CUTFILL["ce_" + CE_MARK[tname]] = "#9fb3c2"
    for p in parts:
        if p["g"] == 8 and p["e"] in ("ceiling", "soffit"):
            p["mc"] = "ce_" + CE_MARK.get(p["name"], "CL1")
    v.draw_parts(boards, sw=0.1)
    w = overlay(sh, v, plane=3000)
    w.draw_parts(WALLS)
    done = set()
    for p in parts:
        if boards(p) and p["obj"] not in done and p["e"] == "ceiling":
            done.add(p["obj"])
            b = obj_bbox(p["obj"])
            c = center(b)
            v.text_uv(c[0], c[1] + 150, CE_MARK.get(p["name"], "CL1"), 1.9, weight=600, color="#1d3a5a")
            v.text_uv(c[0], c[1] - 350, f"+{b[2] / 1000:.2f}", 1.7, color="#1d3a5a")


def r09(sh):
    legend_at(sh, 182, 176, [("#ffffff", "CL1 ยิปซัม 9 มม. ฉาบรอยต่อ ทาสี"), ("#dbe9f2", "CL2 ยิปซัมกันชื้น 9 มม. (ห้องน้ำ / ระเบียง)"),
                             ("#ecdcc0", "CL3 ฝ้าชายคา Smartboard ระบายอากาศ +3.686")], cols=1)
    v = sh.view("front", 100, (-1300, 14300, 500, 4500), (190, 268), plane=-6000, title="รูปตัดแสดงระดับฝ้า  ฉ-ฉ", sub="ตัดที่ y 6.00 · 1:100", tdy=9)
    v.draw_parts(lambda p: p["g"] in (3, 4, 5, 8) and not p.get("rb") and p["e"] not in ("cline",))
    for z, lab in ((3600, "+3.60 ฝ้าห้องทั่วไป"), (3100, "+3.10 ครัว / ระเบียงหลัง"), (800, "+0.80")):
        v.text_uv(14250, z + 40, lab, 1.7, "end", color="#1d3a5a")


late_sheet("ST-09", "ST09", "ผังฝ้า + รูปตัดระดับฝ้า", "ฝ้าเพดาน",
           ["ฝ้าทุกห้อง +3.60 · ครัวและระเบียงหลัง +3.10 ใต้หลังคาเพิง · ฝ้าชายคา Smartboard ระบายอากาศ +3.686",
            "โครงซีไลน์แขวนจากโครงหลังคา ฉากริมผนังทุกห้อง · ฉาบภายในหยุดที่ระดับฝ้า"],
           ["CL1 98.04 · CL2 21.45 · CL3 30.06 ตร.ม.",
            "ซีไลน์ 863 ม. (227 เส้น) · ก้านแขวน 235 จุด · ฉากริมผนัง 165 ม.",
            "ห้องน้ำ / ระเบียงใช้แผ่นกันชื้น"],
           "1:125 / 1:100", p09, r09, cap="โครงซีไลน์ (แผ่นฝ้าโปร่ง)")


# ---------------- ST-10 paint ----------------
def p10(sh):
    v = base_plan(sh, "ผังผิวทาสี  PAINT PLAN", "ตัดที่ระดับ +1.50 · 1:125", plane=1500)
    v.draw_parts(lambda p: WALLS(p) or (p["g"] == 9 and p["e"] != "paint") or (p["g"] == 10 and p["e"] == "wall_tile"))


def r10(sh):
    legend_at(sh, 182, 176, [("#e2b860", "ผิวทาสีผนัง (รองพื้น + ทับหน้า 2 เที่ยว)"), ("#7d8a96", "กระเบื้องผนังห้องน้ำ (ไม่ทาสี)"),
                             ("url(#h-brick)", "ผนังอิฐ (ตัด)")], cols=1)
    elevation(sh, (190, 270), 125, lambda p: p["g"] in (4, 5, 9, 13) and not p.get("rb"), sub="ผิวทาสีภายนอก · 1:125",
              crop=(-1300, 14300, -300, 4600))


late_sheet("ST-10", "ST10", "งานสี", "งานสี",
           ["รองพื้นปูนใหม่ + สีจริง 2 เที่ยว TOA SuperShield ภายนอก/ภายใน · ฝ้ารองพื้น + สี 2 เที่ยว",
            "ผนังห้องน้ำกรุกระเบื้องและโคนผนังใต้ผิวพื้นไม่ทาสี"],
           ["สีภายนอก 193.8 ตร.ม. → 5 ถัง · สีภายใน 204.4 ตร.ม. → 5 ถัง",
            "ฝ้า 149.5 ตร.ม. → รองพื้น 2 + สี 2 ถัง",
            "สีรองพื้นตามสูตรผู้รับเหมา = พื้นที่ฉาบ 470.3 ตร.ม."],
           "1:125", p10, r10, cap="ผิวทาสีด้านหลัง")


# ---------------- ST-11 tiles + steps ----------------
FT_FILL = {"FT_house_Tiles": "#efe9da", "FT_verandah_front_Tiles": "#d5dcc8", "FT_rear_Tiles": "#d5dcc8", "FT_bath": "#c9dce8",
           "FT_Risers": "#d9c3a8", "FT_Step": "#d9c3a8"}


def p11(sh):
    v = base_plan(sh, "ผังวัสดุปูพื้น  FLOOR FINISH PLAN", "มองจากบน · 1:125")
    for p in parts:
        if p["g"] == 10:
            k = next((k for k in FT_FILL if p["obj"].startswith(k)), None)
            if k:
                D.TINT["ft_" + k] = FT_FILL[k]
                D.CUTFILL["ft_" + k] = "#7d8a96"
                p["mc"] = "ft_" + k
    v.draw_parts(lambda p: p["g"] == 10 and p["e"] in ("floor_tile", "riser_tile", "step_tile"), sw=0.05)
    w = overlay(sh, v, plane=1500)
    w.draw_parts(WALLS)


def r11(sh):
    legend_at(sh, 182, 176, [("#efe9da", "FL2 กระเบื้อง 60×60 ผิวมัน +0.80"), ("#d5dcc8", "FL3 60×60 ผิวหยาบ (ระเบียง / ซักล้าง)"),
                             ("#c9dce8", "FL4 40×40 ผิวหยาบ (ห้องน้ำ +0.70)"), ("#d9c3a8", "บันได / ลูกตั้ง FL3")], cols=1)
    v = sh.view("left", 25, (-500, 1700, -400, 1000), (200, 262), plane=-7200, title="รูปตัดบันไดหน้า D1  ช-ช", sub="ตัดที่ x 7.20 · 1:25", tdy=9)
    v.draw_parts(lambda p: p["g"] in (2, 3, 10) and not p.get("rb") and in_box((7000, -1800, -500), (7500, 600, 1100))(p))
    v.uvline((-500, 0), (1700, 0), sw=0.25, dash="3,1")
    v.text_uv(1680, 40, "GL ±0.000", 1.8, "end")
    v.text_uv(-450, 840, "+0.80 ผิวพื้นระเบียง", 1.7, "start", color="#1d3a5a")


late_sheet("ST-11", "ST11", "กระเบื้อง + บันได", "กระเบื้องและบันได",
           ["ปูกระเบื้องบนปูนทรายปรับระดับ ผิวพื้น +0.80 = ผิวกระเบื้อง (ห้องน้ำ +0.70) · ห้องน้ำกันซึมยืดหยุ่น 2 เที่ยว",
            "บันได ค.ส.ล. 3 จุด (หน้า D1 / หลัง / ซักล้าง) ลูกตั้ง 4 × 0.175 ม. ปู FL3"],
           ["FL2 100.87 · FL3 29.56 · FL4 8.24 · ผนังห้องน้ำ 46.10 ตร.ม.",
            "บันได คอนกรีต 1.535 ลบ.ม. · ปูนทรายปรับระดับ 2.10 ลบ.ม.",
            "กระเบื้องนับแผ่นเต็ม + แผ่นตัดจากโมเดล + 3 %"],
           "1:125 / 1:25", p11, r11, cap="บันไดหน้า D1")


# ---------------- ST-12 electrical ----------------
CD_COL = [("CD_L", "#d1453b", "วงจรแสงสว่าง L1–L3"), ("CD_P", "#2b6fd1", "วงจรเต้ารับ P1–P6"), ("CD_AC", "#2f9a5a", "วงจรแอร์ AC1–AC3"),
          ("CD_WH", "#e08a1e", "วงจรน้ำอุ่น WH1–WH2"), ("CD_MAIN", "#111111", "สายเมนจากมิเตอร์")]


def cd_col(m):
    return next((c for k, c, _ in CD_COL if m["n"].startswith(k)), "#666")


def sym(v, kind, x, y):
    X, Y = v.pp(x, y)
    a = v.ann
    if kind == "DL":
        a.append(f'<circle cx="{f(X)}" cy="{f(Y)}" r="0.9" fill="#fff" stroke="#111" stroke-width="0.18"/><circle cx="{f(X)}" cy="{f(Y)}" r="0.3" fill="#111"/>')
    elif kind == "EAVE":
        a.append(f'<circle cx="{f(X)}" cy="{f(Y)}" r="1.0" fill="#fff" stroke="#111" stroke-width="0.18"/><path d="M{f(X - 0.7)} {f(Y - 0.7)}L{f(X + 0.7)} {f(Y + 0.7)}M{f(X + 0.7)} {f(Y - 0.7)}L{f(X - 0.7)} {f(Y + 0.7)}" stroke="#111" stroke-width="0.15"/>')
    elif kind == "SO":
        a.append(f'<circle cx="{f(X)}" cy="{f(Y)}" r="0.8" fill="#fff" stroke="#2b6fd1" stroke-width="0.2"/><line x1="{f(X - 0.8)}" y1="{f(Y)}" x2="{f(X + 0.8)}" y2="{f(Y)}" stroke="#2b6fd1" stroke-width="0.2"/>')
    elif kind == "SW":
        a.append(f'<circle cx="{f(X)}" cy="{f(Y)}" r="0.6" fill="#d1453b"/>')
    elif kind in ("PB", "METER"):
        a.append(f'<rect x="{f(X - 1.2)}" y="{f(Y - 0.6)}" width="2.4" height="1.2" fill="#111"/>')
    elif kind == "WH":
        a.append(f'<rect x="{f(X - 0.9)}" y="{f(Y - 0.9)}" width="1.8" height="1.8" fill="#fff" stroke="#e08a1e" stroke-width="0.2"/>' + text(X, Y + 0.55, "W", 1.2, weight=600, color="#e08a1e"))
    elif kind in ("FCU", "CDU"):
        a.append(f'<rect x="{f(X - 1.4)}" y="{f(Y - 0.6)}" width="2.8" height="1.2" fill="#fff" stroke="#2f9a5a" stroke-width="0.2"/>' + text(X, Y + 0.45, "AC", 1.0, weight=600, color="#2f9a5a"))
    elif kind == "FLUO":
        a.append(f'<rect x="{f(X - 1.6)}" y="{f(Y - 0.35)}" width="3.2" height="0.7" fill="#fff" stroke="#111" stroke-width="0.18"/>')


def el_kind(n):
    for k in ("EAVE", "FLUO", "METER", "FCU", "CDU", "DL", "SO", "SW", "PB", "WH"):
        if n.startswith("EL_" + k):
            return k
    return None


def p12(sh):
    v = base_plan(sh, "ผังไฟฟ้า  ELECTRICAL PLAN", "แสงสว่าง เต้ารับ แอร์ น้ำอุ่น + แนวท่อร้อยสาย · 1:125", plane=1500)
    v.draw_parts(WALLS, color="#777", tint=False)
    draw_lines(v, [m for m in LINES if m["g"] == 12 and m["e"] == "conduit"], cd_col, sw=0.22, dash=lambda m: "1.4,0.6" if "Flex" in m["n"] else None)
    seen = set()
    for obj in [p["obj"] for p in parts if p["g"] in (11, 12)] + [m["n"] for m in MESH if m["g"] == 11]:
        k = el_kind(obj)
        if not k or obj in seen:
            continue
        seen.add(obj)
        b = obj_bbox(obj)
        if b:
            c = center(b); sym(v, k, c[0], c[1])


def r12(sh):
    items = [("#fff", "")] and None
    x, y = 182, 175
    rows = [("DL", "ดาวน์ไลท์ LED 12 W 6\" (38)"), ("EAVE", "โคมซาลาเปาใต้ชายคา (4)"), ("SW", "สวิตช์ทางเดียว (12 ตัว / 11 แผง)"),
            ("SO", "เต้ารับคู่ 3 ขา (28) + กันน้ำ (6)"), ("WH", "เครื่องทำน้ำอุ่น 4,500 W (2)"), ("FCU", "แอร์ 13,000 / 9,000 / 9,000 BTU"),
            ("PB", "ตู้ Square D Classic 18 ช่อง / มิเตอร์")]
    dummy = sh.view("plan", 1, (0, 1, 0, 1), (0, 0))   # paper-coordinate helper for symbols
    dummy.pp = lambda u, w: (u, w)
    for i, (k, lab) in enumerate(rows):
        yy = y + i * 4.6
        sym(dummy, k, x + 3, yy - 0.8)
        sh.add(text(x + 8, yy, lab, 1.95, "start"))
    for i, (_, c, lab) in enumerate(CD_COL):
        yy = y + i * 4.6
        sh.add(f'<line x1="{x + 78}" y1="{yy - 0.8}" x2="{x + 86}" y2="{yy - 0.8}" stroke="{c}" stroke-width="0.5"/>')
        sh.add(text(x + 89, yy, lab, 1.95, "start"))
    brk = next((l for l in REP.get("ST12", []) if l.startswith("ตู้ Schneider")), "")
    cells = [c.strip() for c in brk.split(":", 1)[-1].split("·")] if brk else []
    rows = []
    desc = {"L": "แสงสว่าง", "P": "เต้ารับ", "AC": "แอร์", "WH": "เครื่องทำน้ำอุ่น"}
    for c in cells:
        nm = c.split()[0]
        rows.append((nm, desc.get(nm.rstrip("0123456789"), ""), " ".join(c.split()[1:])))
    half = (len(rows) + 1) // 2
    sh.add(text(182, 214, "ตารางวงจร (ตู้ consumer unit 18 ช่อง + เมน 50 A)", 2.3, "start", 600))
    sh.table(182, 217, [("วงจร", 12), ("ใช้งาน", 26), ("เบรกเกอร์", 41)], rows[:half], size=1.8, rh=3.4)
    sh.table(266, 217, [("วงจร", 12), ("ใช้งาน", 26), ("เบรกเกอร์", 41)], rows[half:], size=1.8, rh=3.4)


late_sheet("ST-12", "ST12", "ระบบไฟฟ้า", "ระบบไฟฟ้า",
           ["อุปกรณ์อ่านจากสัญลักษณ์ในแบบ EE-02/03 (ย้าย 7 จุดที่ทับช่องเปิด/เสาเอ็น) · วงจรและวัสดุตาม BOQ ผู้รับเหมา",
            "ท่อ PVC ร้อยสาย THW เดินบนฝ้า ลงผนังในร่อง · ตู้ Square D Classic 18 ช่อง 14 วงจร + เมน"],
           ["ท่อ 1/2\" 377.6 ม. · กล่อง 4×4 116 ใบ · THW 2.5 12 ขด / 4 2 ขด",
            "เบรกเกอร์กันดูด (RCBO) วงจรห้องน้ำและน้ำอุ่น",
            "แอร์ประเมินจากขนาดห้อง 13,000 / 9,000 / 9,000 BTU"],
           "1:125", p12, r12, cap="แนวท่อร้อยสายบนฝ้า", rep="ST12")


# ---------------- ST-14 doors, windows ----------------
def p14(sh):
    v = base_plan(sh, "ผังประตู หน้าต่าง  DOOR & WINDOW PLAN", "ตัดที่ระดับ +1.50 · 1:125", plane=1500)
    v.draw_parts(lambda p: WALLS(p) or p["g"] == 13)
    seen = set()
    for p in parts:
        if p["g"] == 13 and p["e"] == "frame" and p["obj"] not in seen:
            seen.add(p["obj"])
            mk = p["obj"].split("_")[1]
            b = obj_bbox(p["obj"]); c = center(b)
            horiz = (b[3] - b[0]) > (b[4] - b[1])
            v.text_uv(c[0] + (0 if horiz else 420), c[1] + (420 if horiz else -60), mk, 1.8, weight=600, color="#a33")


def r14(sh):
    rows = [(a, b) for a, b in qty_rows("ST14")[:10]]
    sh.add(text(182, 173, "ตารางประตู หน้าต่าง (นับจากโมเดล)", 2.3, "start", 600))
    sh.table(182, 176, [("แบบ / ขนาด (รวมวงกบ)", 104), ("จำนวน", 14)], [(a, b) for a, b in rows], size=1.75, rh=3.3)
    elevation(sh, (190, 272), 125, lambda p: p["g"] in (4, 5, 9, 13) and not p.get("rb"), sub="ประตูหน้าต่างด้านหน้า · 1:125",
              crop=(-1300, 14300, -300, 4600), tdy=8)


late_sheet("ST-14", "ST14", "ประตู หน้าต่าง", "ประตูและหน้าต่าง",
           ["ขนาดใน A-14/15 = ขนาดรวมวงกบ ช่องอิฐเผื่อ 2 ซม./ด้าน · D1 ไม้เนื้อแข็งบานคู่ลูกฟักกระจก · D2 uPVC บานเลื่อนรางแขวน",
            "D3/D4 uPVC บานเปิด · W1–W5 อลูมิเนียมดำ · W6 ไม้เนื้อแข็งบานเลื่อน"],
           ["ประตู 10 ชุด · หน้าต่าง 16 ชุด ครบตาม BOQ",
            "กระจกใส 5 มม. 16.41 ตร.ม. · บานพับสแตนเลส 4\" 27 ตัว",
            "ซิลิโคนรอบวงกบอลูมิเนียม 2 ด้าน 150 ม."],
           "1:125", p14, r14, cap="ด้านหน้าบ้าน")


# ---------------- ST-16 sanitary ----------------
SN_COL = [("SN_CW", "#2b7bd6", None, "ท่อน้ำดี PVC 13.5 ⌀3/4\" / ⌀1/2\""), ("SN_S", "#7a4a2a", None, "ท่อโสโครก PVC 8.5 ⌀4\""),
          ("SN_W", "#2f9a5a", None, "ท่อน้ำทิ้ง PVC 8.5 ⌀2\""), ("SN_V", "#777777", "1.2,0.7", "ท่อระบายอากาศ ⌀2\"")]


def p16(sh):
    v = base_plan(sh, "ผังระบบประปา สุขาภิบาล  PLUMBING PLAN", "ท่อใต้ดิน/บนฝ้าแสดงรวม · 1:125", plane=1500, crop=(-900, 13900, -900, 14700))
    v.draw_parts(WALLS, color="#777", tint=False)
    v.draw_parts(lambda p: p["g"] == 14 and p["e"] in ("fixture", "struct"), sw=0.12)
    draw_meshes(v, [m for m in MESH if m["g"] == 14], lambda m: "#e7eef2", sw=0.15)
    for k, c, d, _ in SN_COL:
        draw_lines(v, [m for m in LINES if m["g"] == 14 and m["n"].startswith(k)], c, sw=0.3, dash=d)
    for n, lab in (("SN_T1", "ถังบำบัด 1"), ("SN_T2", "ถังบำบัด 2"), ("SN_WTANK", "ถังเก็บน้ำ + ปั๊ม")):
        b = obj_bbox(n)
        if b:
            c = center(b); v.text_uv(c[0], b[1] - 300, lab, 1.7, color="#1d3a5a", weight=600)


def r16(sh):
    for i, (k, c, d, lab) in enumerate(SN_COL):
        yy = 176 + i * 4.6
        da = f' stroke-dasharray="{d}"' if d else ""
        sh.add(f'<line x1="182" y1="{yy - 0.8}" x2="190" y2="{yy - 0.8}" stroke="{c}" stroke-width="0.6"{da}/>')
        sh.add(text(193, yy, lab, 1.95, "start"))
    rows = [r for r in qty_rows("ST16") if not r[0].startswith(("ข้อ", "สาม"))][:8]
    sh.add(text(262, 173, "ถัง บ่อ อุปกรณ์", 2.3, "start", 600))
    st = next((l for l in REP.get("ST16", []) if l.startswith("ถังบำบัด")), "")
    yy = 177
    TH = {"shower": "ฝักบัว", "spray": "สายชำระ", "wc": "ชักโครก", "lav": "อ่างล้างหน้า", "fd": "ตะแกรงระบายน้ำพื้น", "sink": "ซิงก์ล้างจาน"}
    for part in st.split(":", 1)[-1].split("·"):
        w = part.strip().split()
        if w and w[0] in TH:
            part = TH[w[0]] + " " + " ".join(w[1:])
        sh.add(text(262, yy, "• " + part.strip(), 1.85, "start")); yy += 3.4
    sh.add(text(182, 232, "ท่อ (ความยาวจากโมเดล)", 2.3, "start", 600))
    sh.table(182, 235, [("รายการ", 70), ("ความยาว", 92)], rows[:5], size=1.8, rh=3.4)


late_sheet("ST-16", "ST16", "ประปา สุขาภิบาล", "ประปาและสุขาภิบาล",
           ["มิเตอร์ → ถังเก็บน้ำ + ปั๊ม → ห้องน้ำ (ท่อพาดบนฝ้า +3.65 ลงร่องผนัง) / ครัว",
            "ชักโครก → ถังบำบัด DOS CD-1000 ห้องละถัง → บ่อซึม · ซิงก์ → บ่อดักไขมัน → บ่อซึม (2 กลุ่ม)"],
           ["ท่อ 3/4\" 74.8 · 1/2\" 25.4 · 4\" 15.2 · 2\" 45.3 ม.",
            "ท่อน้ำทิ้งลาดตามมาตรฐาน ฝังดิน cover ≥ 0.45 ม.",
            "ท่อระบายอากาศพ้นหลังคา · วาล์ว 15 · air chamber 11 จุด"],
           "1:125", p16, r16, cap="ห้องน้ำ 1 (ผนังโปร่ง)")


# ---------------- ST-18 extras ----------------
EX_LAB = {"EX_Clad_Battens": "ไม้เทียม WPC", "EX_Arch_W": "หัวโค้ง W3", "EX_Screen_Glass": "กระจกกั้นอาบน้ำ", "EX_Yard_Conc": "ลานซักล้าง FL1"}


def p18(sh):
    v = base_plan(sh, "ผังรายการย่อย  MISCELLANEOUS PLAN", "ตัดที่ระดับ +1.50 · 1:125", plane=1500)
    v.draw_parts(lambda p: WALLS(p) or (p["g"] == 15 and not p.get("rb")))
    w = overlay(sh, v)
    w.draw_parts(lambda p: p["g"] == 15 and p["e"] == "concrete")
    for n, lab in EX_LAB.items():
        b = obj_bbox(n)
        if not b:
            continue
        for p in [q for q in parts if q["obj"] == n][:1]:
            pass
        c = center(b)
        v.text_uv(c[0], c[1] - 500, lab, 1.8, weight=600, color="#a33")


def r18(sh):
    rows = qty_rows("ST18")
    sh.add(text(182, 173, "รายการย่อย (จากโมเดล)", 2.3, "start", 600))
    out = []
    for a, b in rows:
        out.append(("\n".join(wrap(a, 46)), "\n".join(wrap(b, 52))))
    sh.table(182, 176, [("รายการ", 76), ("ปริมาณ", 86)], out, size=1.75, rh=3.3)


late_sheet("ST-18", "ST18", "รายการย่อย", "รายการย่อย",
           ["งานที่เหลือตาม skill: ไม้เทียมเสาหน้าบ้าน หัวโค้ง W3 กระจกกั้นอาบน้ำ ลานซักล้าง เซี้ยมมุมปูน คิ้วกระเบื้อง",
            "ที่ไม่ปั้นเป็นรูปทรงพร้อมเหตุผลอยู่ใน ST18_extras_spec.md"],
           ["ไม้เทียม 1.34 ตร.ม. (A-06 เขียนที่เดียว) · ลานซักล้าง 4.42 ตร.ม.",
            "เซี้ยม 411.1 ม. → 165 เส้น · คิ้ว PVC 40.3 ม. → 17 เส้น",
            "กระจกนิรภัย 10 มม. 0.80×1.90 2 บาน"],
           "1:125", p18, r18, cap="ไม้เทียมเสาหน้าบ้าน")
