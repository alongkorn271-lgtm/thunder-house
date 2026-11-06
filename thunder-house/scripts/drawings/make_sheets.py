# -*- coding: utf-8 -*-
"""KK01 drawing set ST00–ST06 (A3, Thai) — every view is derived from the construction model's boxes.
    python make_sheets.py            -> sheets/KK01_ST00-ST06.html (+ per-sheet html for previews)
Inputs: data/model.json (export_drawing_data.py from KK01_Construction.blend), data/build_report.log
(quantity reports of the same build), render/*.png (render_sheets.py)."""
import base64, io, json, os, re, sys
H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(H, "lib"))
import dwg_lib as D
from dwg_lib import Sheet, text, esc, f
from PIL import Image

M = json.load(open(os.path.join(H, "data", "model.json"), encoding="utf-8"))
LOG = open(os.path.join(H, "data", "build_report.log"), encoding="utf-8", errors="replace").read().splitlines()
RENDER = os.path.join(H, "render")
OUT = os.path.join(H, "sheets")
os.makedirs(OUT, exist_ok=True)

# ---------------- grid (FACTS.md) ----------------
GX = [("1", 0), ("2", 3500), ("3", 5000), ("4", 6500), ("5", 9500), ("6", 13000)]
GY = [("G", 0), ("F", 3000), ("E", 4000), ("D", 4500), ("C", 7500), ("B", 9200), ("A", 12200)]

# ---------------- parts from the model ----------------
MC = {"concrete": "conc", "lean_concrete": "lean", "sand": "sand", "precast": "conc", "brick": "brick",
      "plaster": "plaster", "plate": "steel"}
parts, MESH, LINES = [], [], []
MC.update(steel="steel", fascia="wood", sheet="steel", ceiling="plaster", soffit="wood", cline="steel", paint="paint",
          floor_tile="tile", step_tile="tile", riser_tile="tile", wall_tile="tile", elec="equip", jbox="equip", meter="equip",
          frame="steel", sash="steel", glass="glass", door_leaf="wood", hardware="steel", fixture="equip", struct="equip",
          cladding="wood", steel_rail="steel", arch="steel", screen="glass", screen_ch="steel")
for p in M["parts"]:
    if "v" in p:
        V = p["v"]
        MESH.append(dict(n=p["n"], t=p["t"], e=p["e"], g=p["L"], c=p["c"], f=p["f"],
                         v=[(V[i], V[i + 1], V[i + 2]) for i in range(0, len(V), 3)]))
        continue
    if "p" in p and p["L"] > 5:
        LINES.append(dict(n=p["n"], t=p["t"], e=p["e"], g=p["L"], polys=[[(q[i], q[i + 1], q[i + 2]) for i in range(0, len(q), 3)] for q in p["p"]]))
        continue
    if "b" in p:
        b = p["b"]
        for i in range(0, len(b), 6):
            x0, y0, z0, x1, y1, z1 = b[i:i + 6]
            parts.append(dict(id=f"{p['n']}#{i // 6}", obj=p["n"], name=p["t"], g=p["L"], k="box", rx=0,
                              c=[(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2], s=[x1 - x0, y1 - y0, z1 - z0],
                              mc=MC.get(p["e"], "conc"), e=p["e"], mat=""))
    elif "p" in p:                       # rebar polylines -> thin boxes along each straight segment
        d = max(p.get("d", 8), 6)
        for si, s in enumerate(p["p"]):
            for i in range(0, len(s) - 3, 3):
                a, c = s[i:i + 3], s[i + 3:i + 6]
                L = [abs(c[k] - a[k]) for k in range(3)]
                if max(L) < 1:
                    continue
                sz = [max(L[k], d) if L[k] > 1 else d for k in range(3)]
                parts.append(dict(id=f"{p['n']}#{si}.{i}", obj=p["n"], name=p["t"], g=p["L"], k="box", rx=0, rb=True,
                                  c=[(a[k] + c[k]) / 2 for k in range(3)], s=sz, mc="rebar", e=p["e"], mat=""))
D.set_model(parts)
print("parts", len(parts), "rebar", sum(1 for p in parts if p.get("rb")))

# material look (overrides the skill's LiDAR-specific classes)
D.TINT.update(paint="#f3e6c4", tile="#eef0ea", wood="#ead9bd", glass="#d7ecf3", equip="#f2f2f2", conc="#eceae4", lean="#f3f2ee", sand="#f6f0e0", brick="#f4e2d8", plaster="#f7f7f5", steel="#d8dadc", rebar="#3a2a22")
D.CUTFILL.update(paint="#e2b860", tile="#7d8a96", wood="url(#h-wood)", glass="#bfe0ea", equip="#cfcfcf", conc="url(#h-conc)", lean="url(#h-lean)", sand="url(#h-sand)", brick="url(#h-brick)",
                 plaster="#e2e2de", steel="#1e1e1e", rebar="#1a1a1a")
D.mat_class = lambda p: p.get("mc", "conc")
D.DEFS = D.DEFS.replace("</defs>", """
<pattern id="h-lean" patternUnits="userSpaceOnUse" width="1.6" height="1.6"><rect width="1.6" height="1.6" fill="#f0efea"/><circle cx="0.5" cy="0.5" r="0.12" fill="#777"/></pattern>
<pattern id="h-sand" patternUnits="userSpaceOnUse" width="1.2" height="1.2"><rect width="1.2" height="1.2" fill="#f4ecd6"/><circle cx="0.3" cy="0.4" r="0.1" fill="#8a7a55"/><circle cx="0.9" cy="0.95" r="0.08" fill="#8a7a55"/></pattern>
<pattern id="h-brick" patternUnits="userSpaceOnUse" width="1.4" height="1.4" patternTransform="rotate(45)"><rect width="1.4" height="1.4" fill="#f1d3c3"/><line x1="0" y1="0" x2="0" y2="1.4" stroke="#a0523a" stroke-width="0.14"/></pattern>
<pattern id="h-soil" patternUnits="userSpaceOnUse" width="3" height="3" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="3" stroke="#8a7a62" stroke-width="0.12"/></pattern>
</defs>""")

D.set_project(project=["บ้านพักอาศัย คสล. 1 ชั้น", "KK01 บ้านเกาะคา", "แบบ 1.9.8.0 · กริด 13.00 × 12.20 ม."],
              owner=["(ตามสัญญา)"], site=["ม.5 ต.เกาะคา อ.เกาะคา", "จ.ลำปาง"],
              contractor=["(ยังไม่ระบุ)", "เทียบใบเสนอราคา 5 พ.ย. 69"],
              revision="A   5 พ.ย. 69   แบบร่างจากโมเดลก่อสร้าง",
              status="(DRAFT — ต้องให้วิศวกรโยธาตรวจและลงนาม)")

TOTAL = 16
N = chr(10)


def bbox(p):
    return [p["c"][k] - p["s"][k] / 2 for k in range(3)] + [p["c"][k] + p["s"][k] / 2 for k in range(3)]


def in_box(lo, hi, rebar=None, groups=None):
    """predicate: part overlaps the world box lo..hi; optional rebar / group filters"""
    def pr(p):
        if groups is not None and p["g"] not in groups:
            return False
        if rebar is False and p.get("rb"):
            return False
        b = bbox(p)
        return all(b[k] < hi[k] and b[k + 3] > lo[k] for k in range(3))
    return pr


# ---------------- report lines (quantities) ----------------
ANCH = [("ST01", "F1 ขุดดิน"), ("ST02", "P1 คอนกรีตตอม่อ"), ("ST03", "GB คอนกรีตคานคอดิน"), ("ST04", "PS แผ่นพื้น"),
        ("ST05", "C1 คอนกรีตเสา"), ("ST06", "ผนังก่ออิฐมอญ"), ("ST07", "ตะเข้สันเหล็ก"), ("ST08", "กระเบื้อง CPAC"),
        ("ST09", "ฝ้ายิปซัมบอร์ดธรรมดา"), ("ST11", "กระเบื้องพื้นผิวมัน"), ("ST10", "สีรองพื้นผนัง"), ("ST12", "คอยล์ร้อนแอร์"),
        ("ST14", "ประตูไม้เนื้อแข็ง"), ("ST16", "ท่อน้ำดี PVC 13.5 ⌀1/2"), ("ST18", "ผนังแบบ 4")]
REP, cur = {}, None
for ln in LOG:
    if ln.startswith("[") or not ln.strip():
        continue
    for k, a in ANCH:
        if ln.startswith(a):
            cur = k
    if ln.startswith("Info: Saved"):
        break
    if cur and not ln.startswith("ยังไม่ได้ทำ (รอคำตอบ)"):
        REP.setdefault(cur, []).append(ln.strip())


def qty_rows(stage, maxlen=58):
    rows = []
    for ln in REP.get(stage, []):
        if ":" in ln:
            a, b = ln.split(":", 1)
        else:
            a, b = ln, ""
        a = re.sub(r"^(F1|P1|GB|J1|PS|C1)\s+", "", a.strip())
        b = b.strip()
        rows.append((a[:44], b))
    return rows


def wrap(s, n):
    out, line = [], ""
    for w in re.split(r"(\s+)", s):
        if len(line) + len(w) > n and line.strip():
            out.append(line.rstrip()); line = w.lstrip()
        else:
            line += w
    if line.strip():
        out.append(line.rstrip())
    return out


# ---------------- images ----------------
def img(sh, name, x, y, w, h, frame=True):
    p = os.path.join(RENDER, name + ".png")
    if not os.path.exists(p):
        sh.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#f2f3f0" stroke="#bbb" stroke-width="0.2"/>'
               + text(x + w / 2, y + h / 2, f"(ภาพ {name} ยังไม่ได้ render)", 2.4, color="#888"))
        return
    im = Image.open(p).convert("RGB")
    # crop to the frame aspect, centre
    W, Hh = im.size
    ar = w / h
    if W / Hh > ar:
        nw = int(Hh * ar); im = im.crop(((W - nw) // 2, 0, (W - nw) // 2 + nw, Hh))
    else:
        nh = int(W / ar); im = im.crop((0, (Hh - nh) // 2, W, (Hh - nh) // 2 + nh))
    px = int(w * 8)                                   # ~200 dpi at print size
    if im.width > px:
        im = im.resize((px, int(im.height * px / im.width)), Image.LANCZOS)
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=82)
    b64 = base64.b64encode(buf.getvalue()).decode()
    sh.add(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice" href="data:image/jpeg;base64,{b64}"/>')
    if frame:
        sh.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#111" stroke-width="0.25" rx="1.5"/>')


def panel(sh, x, y, w, h, stage, title, lines, highlights):
    """left info card like a presentation board"""
    sh.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#f3f4f1" stroke="#9aa09a" stroke-width="0.3"/>')
    sh.add(text(x + 5, y + 10, stage, 6.2, "start", 600))
    sh.add(text(x + 5 + 6.2 * 0.62 * len(stage) + 3, y + 10, title, 4.2, "start", 600))
    sh.add(f'<line x1="{x + 5}" y1="{y + 13}" x2="{x + w - 5}" y2="{y + 13}" stroke="#111" stroke-width="0.4"/>')
    yy = y + 19
    for ln in lines:
        for l2 in wrap(ln, 62):
            sh.add(text(x + 5, yy, l2, 2.2, "start", 400, "#333")); yy += 3.3
    yy += 2
    sh.add(text(x + 5, yy, "ประเด็นสำคัญ", 2.7, "start", 600)); yy += 4.6
    for hl in highlights:
        sh.add(f'<circle cx="{x + 7}" cy="{yy - 0.8}" r="1.0" fill="#6b7a8a"/>')
        first = True
        for l2 in wrap(hl, 58):
            sh.add(text(x + 10, yy, l2, 2.15, "start", 400)); yy += 3.2
        yy += 0.8
    return yy


def legend(sh, x, y, items):
    for i, (fill, lab) in enumerate(items):
        yy = y + i * 4.4
        sh.add(f'<rect x="{x}" y="{yy - 2.6}" width="6" height="3.2" fill="{fill}" stroke="#111" stroke-width="0.15"/>')
        sh.add(text(x + 8, yy, lab, 2.0, "start"))


def qty_table(sh, x, y, w, stage, maxrows=14, maxh=60):
    rows = qty_rows(stage)[:maxrows]
    cols = [("รายการ (จากโมเดล)", w * 0.38), ("ปริมาณ", w * 0.62)]
    out = []
    used = 3.3
    for a, b in rows:
        bl = wrap(b, int(w * 0.62 / 1.0))
        al = wrap(a, int(w * 0.38 / 1.0))
        n = max(len(bl), len(al))
        if used + n * 3.3 > maxh:
            break
        used += n * 3.3
        out.append(("\n".join(al + [""] * (n - len(al))), "\n".join(bl + [""] * (n - len(bl)))))
    sh.add(text(x, y - 2, "ปริมาณงานจากโมเดล (สุทธิ ยังไม่เผื่อ)", 2.4, "start", 600))
    return sh.table(x, y, cols, out, size=1.75, rh=3.3)


def grids(v, xs=True, ys=True, ext=(6, 6), vals_x=GX, vals_y=GY):
    if xs:
        for n, val in vals_x:
            v.grid(n, val, False, ext=ext)
    if ys:
        for n, val in vals_y:
            v.grid(n, val, True, ext=ext)


def grid_dims(v, below=8, left=8):
    xs = [g[1] for g in GX]
    v.chain(xs, GY[0][1], -below, size=1.7)
    v.dim((xs[0], GY[0][1]), (xs[-1], GY[0][1]), -(below + 5), size=1.8)
    ys = [g[1] for g in GY]
    v.chain(ys, GX[0][1], -left, horiz=False, size=1.7)
    v.dim((GX[0][1], ys[0]), (GX[0][1], ys[-1]), -(left + 5), horiz=False, size=1.8)


PLAN_CROP = (-900, 13900, -900, 13500)     # world mm (x0, x1, y0, y1)


def plan_view(sh, title, sub, plane, pred, at=(36, 214), scale=125):
    v = sh.view("plan", scale, PLAN_CROP, at, plane=plane, title=title, sub=sub, tdy=17)
    v.draw_parts(pred)
    grids(v, ext=(5, 5))
    grid_dims(v, below=8, left=8)
    return v


def mark_objects(v, groups, el, label, size=1.8, every=1, dy=0):
    seen = set()
    for p in parts:
        if p["g"] in groups and p["e"] == el and not p.get("rb") and p["obj"] not in seen:
            seen.add(p["obj"])
            if len(seen) % every:
                continue
            v.text_uv(p["c"][0], p["c"][1] + dy, label, size, weight=600, color="#1d3a5a")


# ===================================================================== sheets
SH = []

# ---------------- ST00 cover ----------------
s0 = Sheet("ST-00", "ปก สารบัญแบบ\nผังกริด หมายเหตุทั่วไป", "ตามระบุ", TOTAL)
img(s0, "cover_house", 14, 14, 200, 133)
img(s0, "cover_exploded", 220, 14, 126, 151)
s0.add(text(16, 156, "KK01 บ้านพักอาศัย คสล. 1 ชั้น · ต.เกาะคา อ.เกาะคา จ.ลำปาง", 5.0, "start", 600))
s0.add(text(16, 162.5, "ชุดแบบก่อสร้างทีละขั้นจากโมเดล 3 มิติ ST00–ST18 — ทุกเส้นและปริมาณสร้างจากโมเดลเดียวกัน", 2.5, "start", 400, "#333"))
v = s0.view("plan", 150, PLAN_CROP, (232, 278))
v.draw_parts(lambda p: p["g"] == 0 and p["e"] == "concrete")
grids(v, ext=(4, 4))
grid_dims(v, below=4, left=4)
s0.add(text(232, 172, "ผังกริดอาคาร  GRID PLAN", 3.2, "start", 600))
s0.add(text(232, 176.5, "มาตราส่วน 1:150 · แสดงฐานราก F1 23 ฐาน", 2.1, "start", 400, "#333"))
s0.table(16, 170, [("แผ่น", 18), ("ชื่อแบบ", 70), ("มาตราส่วน", 26)], [
    ("ST-00", "ปก สารบัญแบบ ผังกริด หมายเหตุทั่วไป", "1:150"), ("ST-01", "ฐานราก F1", "1:125 / 1:25"),
    ("ST-02", "ตอม่อ P1", "1:125 / 1:25"), ("ST-03", "คานคอดิน B1/B2/B3", "1:125 / 1:10"),
    ("ST-04", "พื้น PS + พื้นหล่อในที่ S", "1:125 / 1:20"), ("ST-05", "เสา C1", "1:125 / 1:40"),
    ("ST-06", "ผนังก่ออิฐ เสาเอ็น ทับหลัง ฉาบ", "1:125 / 1:30"), ("ST-07", "โครงหลังคาเหล็ก", "1:125"),
    ("ST-08", "มุงหลังคา + รูปด้านหน้า", "1:125"), ("ST-09", "ผังฝ้า + รูปตัด", "1:125 / 1:100"),
    ("ST-10", "งานสี", "1:125"), ("ST-11", "กระเบื้อง + บันได", "1:125 / 1:25"), ("ST-12", "ระบบไฟฟ้า", "1:125"),
    ("ST-14", "ประตู หน้าต่าง", "1:125"), ("ST-16", "ประปา สุขาภิบาล", "1:125"), ("ST-18", "รายการย่อย", "1:125")], size=1.85, rh=3.6)
s0.para(16, 238, ["§หมายเหตุทั่วไป",
                  "1. หน่วยเป็นมิลลิเมตร ระดับเป็นเมตร อ้างอิง ±0.000 = ระดับดินเดิม (GL)",
                  "2. ระดับ +0.80 / +0.70 (ห้องน้ำ ระเบียง) = ผิวกระเบื้อง; โครงสร้างต่ำกว่าผิว 3 ซม. (หลังคาน +0.67)",
                  "3. คอนกรีต 240 ksc · เหล็ก DB SD40 / RB SR24 · ระยะหุ้มฐานราก 7.5 ซม. คาน/เสา 3 ซม.",
                  "4. ฐานราก F1 1.20×1.20×0.25 ม. ก้นฐานลึก 1.50 ม. บนคอนกรีตหยาบ 5 ซม. + ทรายบดอัด 10 ซม.",
                  "5. ปริมาณในแบบเป็นค่าสุทธิจากโมเดล ยังไม่รวมเผื่อเศษ (ดูไฟล์ BOQ เทียบ)",
                  "6. ตรวจสอบระยะหน้างานก่อนตัดเหล็ก/ตั้งแบบ ห้ามวัดขนาดจากแบบด้วยไม้บรรทัด"], size=2.15, lh=1.55)
s0.para(130, 238, ["§ข้อตีความแบบที่ต้องยืนยัน",
                   "• +4.30 ในแบบ = หลังอะเส → ยอดเสา/ผนังบ้านหลัก +4.175",
                   "• ห้องน้ำ 2 (D5–F5a) เปลี่ยนจาก PS เป็นพื้นหล่อในที่ S",
                   "• Wire mesh 4 มม. @0.10 ตาม S-03 (ใบเสนอราคาใช้ @0.20)",
                   "• แผ่นพื้น PS LL ≥ 250 กก./ตร.ม. ตาม S-03",
                   "• เสาเอ็น/ทับหลังครบทุกช่องเปิด แบ่งแผงไม่เกิน 2.50 ม.",
                   "• แบบร่างจากโมเดล — วิศวกรโยธาต้องตรวจและลงนามก่อนใช้งาน"], size=2.15, lh=1.55)
SH.append(s0)

CALLS = []


def common_bottom(sh, stage, cap, nrows):
    img(sh, f"{stage}_rebar", 292, 124, 54, 39)
    sh.add(text(319, 166.5, cap, 1.8, "middle", 400, "#555"))


def calls(v, items, x=256, top=172, gap=7.0, size=1.9):
    """callouts in a column right of a detail, each at its target height (spread so they never overlap)"""
    pts = sorted(((v.pp(*uv)[1], uv, t) for uv, t in items), key=lambda t: t[0])
    y = top
    for py, uv, t in pts:
        y = max(y, py)
        v.call(uv, x, y, t, size=size)
        y += gap + 2.4 * t.count(N)


# ---------------- generic stage sheet ----------------
def stage_sheet(no, stage, sheet_title, title, desc, highs, plan_args, detail, leg, scale_note):
    sh = Sheet(no, sheet_title, scale_note, TOTAL)
    img(sh, f"{stage}_stage", 178, 14, 168, 100)
    sh.add(text(180, 118, "ภาพ 3 มิติ: งานขั้นนี้แสดงเป็นสี · งานก่อนหน้าแสดงเป็นสีขาว", 1.9, "start", 400, "#555"))
    yy = panel(sh, 14, 14, 160, 58, stage.replace("ST", "ST-"), title, desc, highs)
    v = plan_view(sh, *plan_args)
    detail(sh)
    legend(sh, 128, 232, leg)
    qty_table(sh, 16, 248, 158, stage, 99, maxh=36)
    SH.append(sh)
    return sh, v


# ---------------- ST01 footings ----------------
def det_st01(sh):
    CALLS.clear()
    lo, hi = (3700, 7400, -1800), (6300, 7600, 800)
    v = sh.view("front", 25, (4100, 5800, -1800, 750), (181, 250), plane=-7500, title="รูปตัดฐานราก F1  ก-ก", sub="ผ่านฐานที่ C3 · 1:25", tdy=10)
    v.draw_parts(lambda p: p["g"] in (0, 1, 2) and in_box(lo, hi)(p))
    v.uvline((4100, 0), (5800, 0), sw=0.25, dash="3,1")
    v.text_uv(5780, 40, "GL ±0.000", 1.9, "end")
    v.dim((4400, -1500), (5600, -1500), -9, "1,200")
    v.dim((5600, -1500), (5600, -1250), 6, horiz=False, txt="250")
    v.dim((5600, -1650), (5600, -1500), 12, horiz=False, txt="150")
    CALLS.append(((5000, -500), "ตอม่อ P1 0.20×0.20 (ST-02)"))
    CALLS.append(((4600, -1380), "ฐานราก F1 1.20×1.20×0.25" + N + "DB12 @0.125 สองทาง"))
    CALLS.append(((4500, -1525), "คอนกรีตหยาบ 5 ซม."))
    CALLS.append(((4450, -1610), "ทรายหยาบบดอัด 10 ซม."))
    calls(v, CALLS)
    common_bottom(sh, "ST01", "เหล็กเสริมฐานราก (คอนกรีตโปร่ง)", 9)

s, v = stage_sheet("ST-01", "ST01", "ฐานราก F1", "งานฐานราก",
                   ["ฐานแผ่ F1 23 ฐาน ใต้เสาทุกต้น ก้นฐานลึก 1.50 ม. จากดินเดิม วางบนคอนกรีตหยาบและทรายบดอัด",
                    "หลุมขุดกว้างกว่าฐานข้างละ 0.20 ม. หลุมที่ซ้อนกัน 5 คู่ คิดดินขุดครั้งเดียว"],
                   ["ฐาน 1.20×1.20×0.25 ม. เหล็ก DB12 @0.125 ม. สองทาง ระยะหุ้ม 7.5 ซม.",
                    "คอนกรีต 8.28 ลบ.ม. → สั่ง 8.5 · ดินขุดสุทธิ 95.8 ลบ.ม.",
                    "ตำแหน่งฐานยึดศูนย์กลางเสาตามกริด 1–6 / A–G"],
                   ("ผังฐานราก  FOOTING PLAN", "ตัดที่ระดับ −1.20 · 1:125", -1200, lambda p: p["g"] == 0 and not p.get("rb")),
                   det_st01, [("#eceae4", "คอนกรีต 240 ksc"), ("#f0efea", "คอนกรีตหยาบ"), ("#f4ecd6", "ทรายบดอัด")], "1:125 / 1:25")
mark_objects(v, {0}, "concrete", "F1", dy=-330)

# ---------------- ST02 stubs ----------------
def det_st02(sh):
    CALLS.clear()
    lo, hi = (4300, 6600, -1800), (5700, 8400, 800)
    v = sh.view("left", 25, (-8300, -6700, -1800, 750), (183, 250), plane=-5000, title="รูปตัดตอม่อ P1  ข-ข", sub="ผ่านตอม่อที่ C3 · 1:25", tdy=10)
    v.draw_parts(lambda p: p["g"] in (0, 1, 2) and in_box(lo, hi)(p))
    v.uvline((-8300, 0), (-6700, 0), sw=0.25, dash="3,1")
    v.text_uv(-6720, 40, "GL ±0.000", 1.9, "end")
    v.dim((-7400, -1250), (-7400, 270), 18, horiz=False, txt="1,520")
    v.dim((-7600, 270), (-7400, 270), 5, "200")
    CALLS.append(((-7500, 470), "คานคอดิน (ST-03) หลังคาน +0.67"))
    CALLS.append(((-7500, -200), "ตอม่อ P1 0.20×0.20 −1.25 → +0.27" + N + "6-DB12 ขาตีนช้าง ถึง +1.30" + N + "RB6 @0.15 · หุ้ม 3 ซม."))
    CALLS.append(((-7800, -1380), "ฐานราก F1 (ST-01)"))
    calls(v, CALLS)
    common_bottom(sh, "ST02", "เหล็กยืนตอม่อ + ปลอก", 8)

s, v = stage_sheet("ST-02", "ST02", "ตอม่อ P1", "งานตอม่อ",
                   ["ตอม่อ 23 ต้นจากหลังฐานราก −1.25 ถึงใต้คานคอดิน +0.27 เหล็กยืนต่อขึ้นไปทาบกับเหล็กเสา"],
                   ["ตอม่อ 0.20×0.20 ม. สูง 1.52 ม. · คอนกรีต 1.40 ลบ.ม.",
                    "เหล็กยืน 6-DB12 ยาว 2.865 ม. ขาตีนช้าง 0.20 บนตะแกรงฐาน ถึง +1.30 (หลังคาน + ทาบ 0.60)",
                    "ปลอก RB6 @0.15 ม. 11 ปลอก/ต้น"],
                   ("ผังตอม่อ  STUB PLAN", "ตัดที่ระดับ ±0.00 · 1:125", 0, lambda p: p["g"] in (0, 1) and not p.get("rb")),
                   det_st02, [("#eceae4", "คอนกรีต (ตัด)"), ("#ffffff", "ฐานรากใต้ระดับตัด")], "1:125 / 1:25")

# ---------------- ST03 ground beams ----------------
def det_st03(sh):
    CALLS.clear()
    v = sh.view("left", 10, (-7850, -7150, -120, 820), (180, 230), plane=-4250, title="รูปตัดคานคอดิน  ค-ค", sub="คานแนว C ช่วง 2–3 · 1:10", tdy=10)
    v.draw_parts(lambda p: p["g"] in (2,) and in_box((4000, 7000, -300), (4500, 8000, 900))(p))
    v.uvline((-7850, 0), (-7150, 0), sw=0.25, dash="3,1")
    v.dim((-7600, 270), (-7400, 270), -6, "200")
    v.dim((-7400, 270), (-7400, 670), 8, horiz=False, txt="400")
    CALLS.append(((-7500, 600), "คาน 0.20×0.40 หลังคาน +0.67" + N + "บน 2-DB12 · ล่าง 2-DB12"))
    CALLS.append(((-7450, 450), "ปลอก RB6 @0.15"))
    CALLS.append(((-7500, 245), "คอนกรีตหยาบ 5 ซม."))
    CALLS.append(((-7500, 100), "ทรายบดอัด GL → +0.22"))
    calls(v, CALLS)
    common_bottom(sh, "ST03", "รอยต่อคาน–เสาที่ C3", 8)

s, v = stage_sheet("ST-03", "ST03", "คานคอดิน", "งานคานคอดิน",
                   ["คานคอดิน 19 แนว 53 ช่วง ทุกช่วงขนาด 0.20×0.40 (B1/B2/B3) เทพร้อมข้อต่อคาน–เสา 36 จุด"],
                   ["หลังคาน +0.67 (ใต้ผิวพื้น +0.80 เพื่อเผื่อผิวกระเบื้อง 3 ซม. + ท็อปปิ้ง)",
                    "ทรายบดอัด + คอนกรีตหยาบ 5 ซม. ใต้ท้องคานแทนไม้แบบท้อง",
                    "แนวคานยาวเกิน 10 ม. ทาบเหล็ก 0.60 ม. (12 จุด) · คอนกรีต 9.55 ลบ.ม. → สั่ง 10"],
                   ("ผังคานคอดิน  GROUND BEAM PLAN", "มองจากบน · 1:125", None, lambda p: p["g"] in (2,) and p["e"] == "concrete" and not p.get("rb")),
                   det_st03, [("#eceae4", "คาน + ข้อต่อ (คอนกรีต)")], "1:125 / 1:10")

# ---------------- ST04 floor ----------------
def det_st04(sh):
    CALLS.clear()
    v = sh.view("front", 20, (4350, 5750, 200, 900), (180, 175), plane=-6000, title="รูปตัดพื้น PS บนคาน  ง-ง", sub="ตัดที่ y 6.00 ผ่านคานแนว 3 · 1:20", tdy=10)
    v.draw_parts(lambda p: p["g"] in (2, 3) and in_box((4200, 5500, 150), (5900, 6600, 950))(p))
    CALLS.append(((4500, 750), "ท็อปปิ้ง ถึง +0.77" + N + "wire mesh 4 มม. @0.10"))
    CALLS.append(((5300, 695), "แผ่นพื้นสำเร็จ PS 0.35×0.05" + N + "LL ≥ 250 กก./ตร.ม."))
    CALLS.append(((5000, 470), "คานคอดิน 0.20×0.40"))
    calls(v, CALLS)
    common_bottom(sh, "ST04", "ตะแกรงพื้น + พื้น S ห้องน้ำ", 10)

s, v = stage_sheet("ST-04", "ST04", "พื้น PS + พื้นหล่อในที่ S", "งานพื้น",
                   ["พื้นสำเร็จรูป PS 93 แผ่นบนคานคอดิน เทท็อปปิ้งถึง +0.77 · ห้องน้ำ/ระเบียงเป็นพื้นหล่อในที่ S หนา 0.125 ที่ +0.67"],
                   ["PS 0.35×0.05 ม. LL ≥ 250 กก./ตร.ม. (S-03) 91.15 ตร.ม.",
                    "ท็อปปิ้ง 6.19 ลบ.ม. + wire mesh 4 มม. @0.10 · พื้น S RB9 3.26 ลบ.ม.",
                    "เว้นช่องเสา 23 ต้น · ท็อปปิ้งไม่ยื่นเข้าห้องน้ำ (ขั้นลง 3 ซม.)"],
                   ("ผังพื้น  FLOOR PLAN", "มองจากบน · 1:125", None, lambda p: p["g"] in (2, 3) and not p.get("rb") and (p["g"] == 3 or p["e"] == "concrete")),
                   det_st04, [("#eceae4", "แผ่นพื้น PS / พื้น S / ท็อปปิ้ง"), ("#ffffff", "คาน (ใต้พื้น)")], "1:125 / 1:20")

# ---------------- ST05 columns ----------------
def det_st05(sh):
    CALLS.clear()
    v = sh.view("front", 45, (4500, 5500, -1650, 4300), (186, 272), plane=-7500, title="รูปตัดเสา C1", sub="เสา C3 · 1:45", tdy=9)
    v.draw_parts(lambda p: p["g"] in (0, 1, 2, 3, 4) and in_box((4300, 7400, -1800), (5700, 7600, 4500))(p))
    v.uvline((4500, 0), (5500, 0), sw=0.25, dash="3,1")
    for z, lab in ((4175, "+4.175 ยอดเสา"), (800, "+0.80 ผิวพื้น"), (0, "±0.00 GL"), (-1500, "−1.50 ก้นฐาน")):
        v.text_uv(5480, z + 30, lab, 1.8, "start")
    CALLS.append(((5000, 4240), "แผ่นเหล็กหัวเสา PL 160×160×6"))
    CALLS.append(((5000, 2400), "เสา C1 0.20×0.20 +0.70 → +4.175" + N + "4-DB12 ทาบเหล็กยืนตอม่อ" + N + "ปลอก RB6 @0.15"))
    calls(v, CALLS)
    common_bottom(sh, "ST05", "เหล็กเสาทาบเหล็กยืนตอม่อ", 6)

s, v = stage_sheet("ST-05", "ST05", "เสา C1", "งานเสา",
                   ["เสา 23 ต้นจากผิวคาน/พื้นถึงใต้อะเส บ้านหลักยอด +4.175 แถว A/B ยอด +3.175 ใต้เหล็กรับจันทันเพิง"],
                   ["เสา 0.20×0.20 ม. 4-DB12 ทาบเหล็กยืนตอม่อ · ปลอก RB6 @0.15 ม.",
                    "+4.30 ในแบบ = หลังอะเส 2[]125 → ยอดเสา +4.175",
                    "แผ่นเหล็กหัวเสา PL 160×160×6 ฝังพุก รับอะเส · คอนกรีต 2.98 ลบ.ม."],
                   ("ผังเสา  COLUMN PLAN", "ตัดที่ระดับ +1.50 · 1:125", 1500, lambda p: p["g"] in (2, 4) and not p.get("rb") and p["e"] != "plate"),
                   det_st05, [("#eceae4", "เสา (ตัด)"), ("#ffffff", "คานคอดินใต้ระดับตัด")], "1:125 / 1:40")
mark_objects(v, {4}, "concrete", "C1", dy=-300)

# ---------------- ST06 walls ----------------
def det_st06(sh):
    CALLS.clear()
    v = sh.view("left", 30, (-900, 600, 500, 4300), (190, 268), plane=-2500, title="รูปตัดผนัง  จ-จ", sub="ผ่านหน้าต่าง W3 แนว G ที่ x 2.50 · 1:30", tdy=10)
    v.draw_parts(lambda p: p["g"] in (2, 3, 5) and in_box((2300, -900, 400), (2800, 600, 4400))(p))
    for z, lab in ((4175, "+4.175"), (2920, "+2.92 หัวช่อง"), (980, "+0.98 ธรณี"), (800, "+0.80")):
        v.text_uv(-380, z + 30, lab, 1.7, "start")
    v.text_uv(-60, 1950, "ช่องหน้าต่าง W3 (ST-14)", 1.8, "middle", color="#555", rot=-90)
    CALLS.append(((0, 4000), "ผนังอิฐมอญครึ่งแผ่น 7 ซม." + N + "ฉาบเรียบ 1.5 ซม. สองด้าน"))
    CALLS.append(((0, 2990), "ทับหลังเหนือช่องเปิด 0.07×0.10"))
    CALLS.append(((0, 930), "ทับหลังใต้ธรณีหน้าต่าง"))
    CALLS.append(((0, 700), "ผนังเริ่มบนคานคอดิน/ท็อปปิ้ง"))
    calls(v, CALLS)
    common_bottom(sh, "ST06", "เสาเอ็น/ทับหลัง (ผนังโปร่ง)", 6)

s, v = stage_sheet("ST-06", "ST06", "ผนังก่ออิฐ เสาเอ็น ทับหลัง ฉาบ", "งานผนัง",
                   ["ผนังอิฐมอญครึ่งแผ่น 19 แนว ช่องเปิด 26 ช่อง เสาเอ็น/ทับหลังรอบช่องเปิดและแบ่งแผงไม่เกิน 2.50 ม."],
                   ["อิฐ 3.5×7×16 ซม. 201.5 ตร.ม. → 27,659 ก้อน (รวมแตก 5 %)",
                    "เสาเอ็น/ทับหลัง 0.07×0.10 รวม 325.5 ม. RB6",
                    "ช่องอิฐ = ขนาดวงกบ + 2 ซม./ด้าน · ฉาบในหยุดที่ระดับฝ้า"],
                   ("ผังผนัง  WALL PLAN", "ตัดที่ระดับ +1.50 · 1:125", 1500, lambda p: p["g"] in (4, 5) and not p.get("rb") and p["e"] in ("brick", "concrete") and p["mc"] != "plate"),
                   det_st06, [("#f1d3c3", "อิฐมอญ (ตัด)"), ("#eceae4", "เสา / เสาเอ็น (ตัด)")], "1:125 / 1:25")

exec(open(os.path.join(H, "sheets_late.py"), encoding="utf-8").read())

# ---------------- write ----------------
FONTDIR = os.path.join(H, "lib", "fonts") + os.sep
html = D.page_html(SH, fontdir=FONTDIR)
open(os.path.join(OUT, "KK01_ST00-ST18.html"), "w", encoding="utf-8").write(html)
for sh in SH:
    open(os.path.join(OUT, f"_{sh.no}.html"), "w", encoding="utf-8").write(D.page_html([sh], fontdir=FONTDIR))
print("sheets", [s.no for s in SH])
