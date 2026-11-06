# Build the contractor-vs-model comparison workbook (Thai) from the artifact's data tables.
import json, re, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.utils import get_column_letter

TPL, OUT = sys.argv[1], sys.argv[2]
src = open(TPL, encoding="utf-8").read()


def js_array(name):
    a = src.index(f"const {name} = [")
    i, depth = src.index("[", a), 0
    for j in range(i, len(src)):
        depth += {"[": 1, "]": -1}.get(src[j], 0)
        if depth == 0:
            return json.loads(src[i:j + 1])


def js_key(key):
    a = src.index(f"  {key}: [")
    i, depth = src.index("[", a), 0
    for j in range(i, len(src)):
        depth += {"[": 1, "]": -1}.get(src[j], 0)
        if depth == 0:
            return json.loads(src[i:j + 1])


BOQ, WASTE_TXT = js_array("BOQ"), js_array("WASTE")
MISSING, ASK = js_key("missing"), js_key("ask")

F = "Tahoma"
f_base, f_b, f_h = Font(name=F, size=10), Font(name=F, size=10, bold=True), Font(name=F, size=13, bold=True)
f_in, f_link = Font(name=F, size=10, color="0000FF"), Font(name=F, size=10, color="008000")
f_small = Font(name=F, size=9, color="5B6876")
fill_hdr, fill_grp = PatternFill("solid", fgColor="1D2A37"), PatternFill("solid", fgColor="EEF0EA")
fill_key = PatternFill("solid", fgColor="FFFF00")
fill_ok, fill_bad, fill_na = PatternFill("solid", fgColor="E3F1E8"), PatternFill("solid", fgColor="FBE4DA"), PatternFill("solid", fgColor="F2F2F2")
thin = Side(style="thin", color="C8CEC5")
box = Border(top=thin, bottom=thin, left=thin, right=thin)
wrap = Alignment(wrap_text=True, vertical="top")
NUM, MONEY, PCT = '#,##0.00;(#,##0.00);"-"', '#,##0;(#,##0);"-"', '0%;-0%;"-"'

wb = Workbook()


def header(ws, row, cols):
    for c, t in enumerate(cols, 1):
        x = ws.cell(row, c, t)
        x.font, x.fill, x.alignment, x.border = Font(name=F, size=10, bold=True, color="FFFFFF"), fill_hdr, Alignment(wrap_text=True, vertical="center"), box


def widths(ws, ws_):
    for i, w in enumerate(ws_, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


# ---------------- sheet: waste factors (inputs)
wz = wb.active
wz.title = "อัตราเผื่อ"
wz["A1"], wz["A1"].font = "อัตราเผื่อที่ใช้กับปริมาณจากโมเดล", f_h
wz["A2"], wz["A2"].font = "ตัวเลขสีน้ำเงิน = ค่าที่แก้ได้ · แก้แล้วแผ่น “ต่อรอง” และ “สรุป” คำนวณใหม่เอง", f_small
header(wz, 4, ["รหัส", "หมวดวัสดุ", "อัตราเผื่อ", "หมายเหตุ"])
WASTE = [("concrete", "คอนกรีต (ทุกชนิด)", 0.05, ""), ("sand", "ทราย / คอนกรีตหยาบ", 0.10, ""),
         ("rebar", "เหล็กเสริม", 0.05, "เพิ่มจากจำนวนเส้นที่ได้จากแผนตัด (เศษตัดนับแล้ว)"),
         ("form", "ไม้แบบ", 0.05, ""), ("steel", "เหล็กรูปพรรณ / ระแนง", 0.05, "เพิ่มจากจำนวนเส้นที่ได้จากแผนตัด"),
         ("paint_steel", "ทาสีกันสนิม", 0.05, ""), ("roof_tile", "กระเบื้องหลังคา / ครอบ", 0.0, "รวมในจำนวนแผ่นโมเดลแล้ว (5 % / 3 %)"),
         ("sheet", "เมทัลชีท / เชิงชาย / รางน้ำ", 0.05, ""), ("wall", "ผนัง / ฉาบ / สี / เสาเอ็น / เซี้ยม", 0.05, ""),
         ("finish", "ฝ้า / กระเบื้องพื้น / ผนัง", 0.05, ""), ("pipe", "ท่อประปา / สุขาภิบาล", 0.10, ""),
         ("unit", "ประตู หน้าต่าง อุปกรณ์ สุขภัณฑ์ (นับชุด)", 0.0, "")]
WROW = {}
for i, (k, n, v, note) in enumerate(WASTE):
    r = 5 + i
    WROW[k] = r
    for c, val in enumerate((k, n, v, note), 1):
        x = wz.cell(r, c, val)
        x.font, x.border, x.alignment = f_base, box, wrap
    wz.cell(r, 3).font, wz.cell(r, 3).number_format, wz.cell(r, 3).fill = f_in, PCT, fill_key
widths(wz, [14, 40, 12, 50])

# ---------------- sheet: negotiation (numeric, formulas)
wn = wb.create_sheet("ต่อรอง")
wn["A1"], wn["A1"].font = "จุดต่อรอง: ใบเสนอราคา ผรม. เทียบปริมาณโมเดล (เผื่อแล้ว)", f_h
wn["A2"], wn["A2"].font = ("มูลค่า = (ปริมาณ ผรม. − ปริมาณโมเดลเผื่อแล้ว) × ราคาต่อหน่วยของ ผรม. (ของ + แรง) · "
                           "บวก = ผรม. คิดเกิน · ลบ = ผรม. คิดขาด/ต่ำกว่าแบบ · ตัวเลขสีน้ำเงินแก้ได้"), f_small
H = ["รายการ", "หน่วย", "ปริมาณ ผรม.", "ราคาต่อหน่วย ผรม. (บาท)", "โมเดล สุทธิ", "หมวดเผื่อ", "อัตราเผื่อ",
     "ปัดขึ้นเป็นจำนวนเต็ม", "โมเดล เผื่อแล้ว", "ผลต่าง (ผรม. − โมเดล)", "มูลค่า (บาท)", "ที่มา / หมายเหตุ"]
header(wn, 4, H)
NEGROWS = [  # item, unit, ctr qty, ctr price, model net, waste key, round up, note — ตัวอย่าง (SAMPLE)
    ("ฉาบปูน", "ตร.ม.", 600, 240, 470.32, "wall", 0, "ตัวอย่าง: ราคา ผรม. ของ + แรง"),
    ("จันทัน C100", "เส้น", 60, 800, 26, "steel", 1, "ตัวอย่าง: ความยาวจากโมเดล ÷ 6 ม."),
    ("คอนกรีตตอม่อ + เสา", "ลบ.ม.", 6, 2900, 4.377, "concrete", 0, "ตัวอย่าง"),
    ("เสาเอ็น / ทับหลัง", "ม.", 120, 120, 325.5, "wall", 0, "ตัวอย่าง: ผรม. ขาด → ค่าติดลบ"),
]
r0 = 5
for i, (n, u, cq, cp, mn, wk, ru, note) in enumerate(NEGROWS):
    r = r0 + i
    vals = [n, u, cq, cp, mn, wk, f"='อัตราเผื่อ'!C{WROW[wk]}", ru,
            f"=IF(H{r}=1,ROUNDUP(E{r}*(1+G{r}),0),E{r}*(1+G{r}))", f"=C{r}-I{r}", f"=ROUND(J{r}*D{r},0)", note]
    for c, v in enumerate(vals, 1):
        x = wn.cell(r, c, v)
        x.font, x.border, x.alignment = f_base, box, wrap
    for c in (3, 4, 5, 8):
        wn.cell(r, c).font = f_in
    wn.cell(r, 7).font = f_link
    for c, fmt in ((3, NUM), (4, MONEY), (5, NUM), (7, PCT), (9, NUM), (10, NUM), (11, MONEY)):
        wn.cell(r, c).number_format = fmt
rN = r0 + len(NEGROWS) - 1
# fixed-value items (spec compliance / errors)
rc = rN + 2
wn.cell(rc, 1, "รายการที่ต่ำกว่าแบบ (คิดเป็นเงินก้อน)").font = f_b
FIX = [("ตัวอย่าง: เหล็กตะเข้/ดั้งต้องเป็นขนาดตามแบบ", "เส้น", 10, "=1050-850", "ส่วนต่างราคาต่อเส้นของ ผรม. (2C125 1,050 − 2C100 850)"),
       ("ตัวอย่าง: แผ่นพื้น PS ตาม LL ในแบบ", "ตร.ม.", 100, None, "ให้ ผรม. เสนอราคาส่วนต่าง — ห้ามลดตามแบบ S-03"),
       ("ตัวอย่าง: Wire mesh ระยะตามแบบ", "ตร.ม.", 100, None, "ตามแบบ S-03 หรือให้วิศวกรอนุมัติ @0.20 เป็นลายลักษณ์อักษร")]
header(wn, rc + 1, ["รายการ", "หน่วย", "ปริมาณ", "ส่วนต่างต่อหน่วย (บาท)", "", "", "", "", "", "", "มูลค่า (บาท)", "หมายเหตุ"])
fix_rows = []
for i, (n, u, q, d, note) in enumerate(FIX):
    r = rc + 2 + i
    fix_rows.append(r)
    for c, v in ((1, n), (2, u), (3, q), (4, d), (11, f"=IF(D{r}=\"\",0,-C{r}*D{r})"), (12, note)):
        x = wn.cell(r, c, v)
        x.font, x.border, x.alignment = f_base, box, wrap
    wn.cell(r, 3).font = wn.cell(r, 4).font = f_in
    wn.cell(r, 4).number_format = wn.cell(r, 11).number_format = MONEY
    if d is None:
        wn.cell(r, 4).fill = fill_key
        wn.cell(r, 4).comment = Comment("ใส่ส่วนต่างราคาต่อหน่วยที่ ผรม. เสนอ", "KK01")
rw = fix_rows[-1] + 2
wn.cell(rw, 1, "ใบเสนอราคาคิดเงินผิด").font = f_b
for c, v in ((1, "ตัวอย่าง: รายการที่คิดเงินผิด (จำนวน × ราคา ≠ จำนวนเงิน)"), (2, "ชุด"), (3, 2), (4, 1000), (10, 1000),
             (11, f"=-(C{rw + 1}*D{rw + 1}-J{rw + 1})"), (12, "ผรม. น่าจะขอแก้ภายหลัง — ตกลงให้ชัดว่าราคารวมนี้รวม W4 ครบ")):
    x = wn.cell(rw + 1, c, v)
    x.font, x.border, x.alignment = f_base, box, wrap
wn.cell(rw + 1, 10).comment = Comment("จำนวนเงินที่ใบเสนอราคาเขียนไว้", "KK01")
for c in (4, 10, 11):
    wn.cell(rw + 1, c).number_format = MONEY
widths(wn, [36, 7, 11, 13, 11, 11, 9, 9, 11, 12, 13, 46])
wn.freeze_panes = "B5"
R_W4 = rw + 1

# ---------------- sheet: summary
ss = wb.create_sheet("สรุป", 0)
ss["A1"], ss["A1"].font = "KK01 บ้านเกาะคา — ใบเสนอราคา ผรม. เทียบปริมาณจากโมเดล", f_h
ss["A2"], ss["A2"].font = "ใบเสนอราคา ผรม. ลงวันที่ 5 พ.ย. 69 · โมเดลก่อสร้าง KK01_Construction.blend (ST01–ST18, build 5 พ.ย. 69) · แบบร่าง (DRAFT)", f_small
rows = [
    ("ราคา ผรม. ก่อนส่วนลด", 1020000.0, "ใบเสนอราคา ผรม. หน้า 1 “รวมเป็นเงิน”"),
    ("ส่วนลด", -20000.0, "ใบเสนอราคา ผรม. หน้า 1"),
    ("ราคา ผรม. สุทธิ", "=B4+B5", ""),
    ("ปริมาณที่ ผรม. คิดเกิน (เผื่อแล้ว)", f"=SUMIF('ต่อรอง'!K{r0}:K{rN},\">0\")", "ผลรวมมูลค่าบวกในแผ่น “ต่อรอง”"),
    ("ปริมาณที่ ผรม. คิดขาด", f"=SUMIF('ต่อรอง'!K{r0}:K{rN},\"<0\")", "ผลรวมมูลค่าลบในแผ่น “ต่อรอง”"),
    ("รายการต่ำกว่าแบบ (ที่มีราคา)", f"=SUM('ต่อรอง'!K{fix_rows[0]}:K{fix_rows[-1]})", "PS LL250 / wire mesh ยังไม่มีราคา"),
    ("รายการคิดเงินผิด", f"='ต่อรอง'!K{R_W4}", ""),
    ("ส่วนที่เหลือไว้ต่อรอง", "=SUM(B7:B10)", "ก่อนรวมรายการที่ยังไม่มีในใบเสนอราคา (แผ่น “รายการขาด”)"),
]
header(ss, 3, ["รายการ", "บาท", "ที่มา"])
for i, (a, b, c) in enumerate(rows):
    r = 4 + i
    for col, v in ((1, a), (2, b), (3, c)):
        x = ss.cell(r, col, v)
        x.font, x.border, x.alignment = f_base, box, wrap
    ss.cell(r, 2).number_format = MONEY
    ss.cell(r, 2).font = f_in if isinstance(b, float) else (f_link if "ต่อรอง" in str(b) else f_base)
ss.cell(11, 1).font = ss.cell(11, 2).font = f_b
ss.cell(11, 2).fill = fill_key
ss["A13"], ss["A13"].font = "วิธีอ่าน", f_b
notes = ["ฝั่ง ผรม. ใช้ปริมาณและราคาต่อหน่วยตามใบของเขา ฝั่งเราใช้ปริมาณจริงที่ถอดจากโมเดล + อัตราเผื่อ (แผ่น “อัตราเผื่อ”)",
         "ใช้ส่วนที่คิดเกินเป็นคำถาม “คิดจากอะไร” ถ้าลดไม่ได้ ให้แลกเป็นรายการที่ขาดและของที่ขอเพิ่ม",
         "รายการต่ำกว่าแบบ (PS LL250, wire mesh, เสาเอ็น, 2C125) ต้องได้ตามแบบ ไม่ใช่ของแถม",
         "งานโครงสร้างต้องให้วิศวกรโยธาตรวจและลงนามก่อนใช้ก่อสร้างจริง"]
for i, t in enumerate(notes):
    ss.cell(14 + i, 1, f"{i + 1}. {t}").font = f_base
widths(ss, [44, 16, 70])

# ---------------- sheet: line-by-line comparison
wl = wb.create_sheet("เทียบรายบรรทัด")
wl["A1"], wl["A1"].font = "ไล่ตามรายการในใบเสนอราคา ผรม. ทุกบรรทัด", f_h
wl["A2"], wl["A2"].font = "โมเดลแสดงเป็น “สุทธิ → เผื่อแล้ว” · เหล็กรูปพรรณนับ C เดี่ยวยาว 6 ม. (2C = 2 เส้น)", f_small
header(wl, 4, ["รายการตามใบ ผรม.", "ผรม.", "โมเดล (ปริมาณจริง)", "สถานะ", "หมายเหตุ"])
r = 5
ST = {1: ("ใกล้เคียง", fill_ok), 0: ("ต่างกัน ควรถาม", fill_bad), 2: ("เทียบไม่ได้ / ไม่ได้ถอด", fill_na)}
for row in BOQ:
    if len(row) == 1:
        x = wl.cell(r, 1, row[0])
        x.font = f_b
        for c in range(1, 6):
            wl.cell(r, c).fill = fill_grp
        wl.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
    else:
        t, f = ST[row[3]]
        for c, v in enumerate((row[0], row[1], row[2], t, row[4] if len(row) > 4 else ""), 1):
            x = wl.cell(r, c, v)
            x.font, x.border, x.alignment = f_base, box, wrap
        wl.cell(r, 4).fill = f
    r += 1
widths(wl, [36, 24, 34, 20, 50])
wl.freeze_panes = "A5"

# ---------------- sheet: missing + asks
wm = wb.create_sheet("รายการขาด")
wm["A1"], wm["A1"].font = "รายการที่ยังไม่มีในใบเสนอราคา และของที่ขอเพิ่ม", f_h
header(wm, 3, ["ลำดับ", "รายการที่ต้องให้ ผรม. ใส่เพิ่ม", "หมายเหตุ"])
for i, (a, b) in enumerate(MISSING):
    for c, v in ((1, i + 1), (2, a), (3, b)):
        x = wm.cell(4 + i, c, v)
        x.font, x.border, x.alignment = f_base, box, wrap
ra = 4 + len(MISSING) + 1
header(wm, ra, ["ลำดับ", "ของที่ขอเพิ่ม (แลกกับส่วนที่คิดเกิน)", "หมายเหตุ"])
for i, (a, b) in enumerate(ASK):
    for c, v in ((1, i + 1), (2, a), (3, b)):
        x = wm.cell(ra + 1 + i, c, v)
        x.font, x.border, x.alignment = f_base, box, wrap
rb = ra + len(ASK) + 2
wm.cell(rb, 2, "อื่น ๆ ที่ต้องตกลงให้ชัด").font = f_b
OTHER = ["ตัวอย่าง: รายการที่ใบเสนอราคาระบุว่าไม่รวม (หมายเหตุท้ายใบ)",
         "ตัวอย่าง: วัสดุประตู/หน้าต่าง/พื้นในใบต่างจากแบบ — ตกลงให้ชัดว่ารับได้หรือไม่",
         "ไฟฟ้าคิดเป็นราคาต่อจุด — ยืนยันว่ารวมท่อ PVC สาย THW บล็อก และหน้ากากแล้ว",
         "ตัวอย่าง: รายการที่ใบเว้นจำนวน — ถามว่ารวมในรายการอื่นหรือไม่"]
for i, t in enumerate(OTHER):
    x = wm.cell(rb + 1 + i, 2, t)
    x.font, x.alignment = f_base, wrap
widths(wm, [7, 60, 60])

for ws in wb.worksheets:
    ws.sheet_view.showGridLines = False
    for row in ws.iter_rows():
        for c in row:
            if c.font is None or c.font.name != F:
                c.font = Font(name=F, size=c.font.size if c.font else 10, bold=c.font.b if c.font else False,
                              color=c.font.color if c.font else None)
wb.save(OUT)
print("saved", OUT, "neg rows", r0, rN, "fix", fix_rows, "w4", R_W4)
