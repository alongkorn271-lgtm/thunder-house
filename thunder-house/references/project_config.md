# สิ่งที่ต้องเปลี่ยนเมื่อใช้กับโปรเจกต์ใหม่

สคริปต์ทุกตัวเป็นตัวจริงของ KK01 บ้านเกาะคา คัดลอกไปไว้ในโปรเจกต์ (`Construction/scripts/`, `Construction/drawings/`,
หน้าเว็บใน scratchpad) แล้วแก้เฉพาะจุดเหล่านี้ ค่าที่เหลือเป็นค่ากลางที่ใช้ได้กับบ้าน คสล. 1 ชั้นทั่วไป

## scripts/model (โมเดลก่อสร้าง)
- `kk01_struct.py`: กริด (`GRID`), ฐานราก, ตอม่อ · ไฟล์อื่นตามขั้น: ตารางคาน ผนัง ช่องเปิด ห้อง (`ROOMS` ใน `kk01_ceiling.py`) ฯลฯ
- ชื่อ collection `KK01 STxx ...` และคำนำหน้าออบเจกต์ (`F1_`, `GB_`, `C1_`, `WL_`, `RF_`, `UN_`, `SN_`, `FN_`) — เปลี่ยนชื่อโปรเจกต์ได้ แต่ต้องเปลี่ยนให้ครบทุกไฟล์
- `kk01_furniture.py`: ตำแหน่งเฟอร์นิเจอร์ทุกชิ้นเป็นพิกัดจริงของบ้าน KK01 — บ้านใหม่ต้องวางใหม่จาก `q_rooms.py`

## export_model_json.py
- `LAYERS` — คู่ (ค่าคงที่ collection จาก loader, ป้ายชั้นงาน) เรียงตามขั้น
- `SKIP_EL` — element ที่ไม่ต้องแสดง (ดินขุด สีชั้นรอง ปูนกาว …); ข้อยกเว้น `tile_bed` ใน ST08
- เหล็กเสริม (`rb=1`) = curve ใน collection โครงสร้าง ST01–ST06

## render_sheets.py
- `COL` — ชื่อ collection เต็ม (`"KK01 ST01 Footings"` …) · `CX, CY` ศูนย์กลางแปลน · `ISO` ทิศกล้อง
- `ACCENT` สีประจำขั้น · `STAGE_CAM` ortho_scale ต่อขั้น
- shot รายละเอียด (`*_rebar`, `*_detail`) — ตำแหน่งเป้ากล้องหาจาก bbox ใน model.json (ฐานที่จุดกริด, ห้องน้ำ, บันไดหน้า, ไม้เทียม)

## viewer/template.html
- ชื่อโครงการ/คำบรรยายใน `<h1>`/`<p>` และ `<title>`
- `mainDims` (ข้อมูลหลัก), `BOQ` (รายบรรทัดตามใบ ผรม.), `WASTE`, `NEG` (over/under/missing/ask), `ISSUES`
- `VIEWS` ตำแหน่งกล้อง (`CX`, `CZ` = ศูนย์กลาง; three ใช้ (x, z, −y) หน่วยเมตร)
- build_site.py: `ANCH` = บรรทัดแรกของ report แต่ละขั้น (ใช้แบ่ง log เป็นขั้น)

## boq_parse.py
- `BANDS` = ช่วง x ของคอลัมน์ในหน้า PDF (ชื่อ / จำนวน / หน่วย / ราคาของ / เงินของ / ราคาแรง / เงินแรง / รวม) — ดูจากบรรทัดตัวอย่างใน rows.txt แล้วปรับ
- บรรทัดหัวหมวดอ่านเป็นแถวที่ไม่มีจำนวน — ตรวจผลรวมหมวดด้วยมืออีกรอบ (ตัว parser รวมหัวหมวดผิดได้)

## make_xlsx.py
- `NEGROWS` (รายการ หน่วย ปริมาณ ผรม. ราคา ผรม. โมเดลสุทธิ หมวดเผื่อ ปัดขึ้น หมายเหตุ), `FIX` (ต่ำกว่าแบบ), แถว W4/ผิดเลข
- `rows` ของแผ่นสรุป (ราคาก่อน/หลังส่วนลดจากหน้า 1 ของใบ)

## make_sheets.py / sheets_late.py
- `GX`, `GY` กริดจาก FACTS.md · `PLAN_CROP` · `set_project(...)` หัวกระดาษ · `TOTAL`
- `ANCH` แบ่ง report · ข้อความกล่องข้อมูล/ประเด็นสำคัญ (ตัวเลขจาก report)
- ระนาบตัดรายละเอียด (`plane=`, crop, `in_box`) — หาใหม่จากโมเดลทุกโปรเจกต์ (ดู drawing_sheets.md)
- ป้ายชื่อจากชื่อ object (`UN_W1_…` → W1, `CE_bed1_Board` → CL1) — ถ้า naming ต่าง ให้แก้ฟังก์ชันอ่านชื่อ

## โครงโฟลเดอร์ผลงาน (KK01)
```
Construction/
  scripts/export_drawing_data.py, render_sheets.py
  drawings/  make_sheets.py  sheets_late.py  render_pdf.py  lib/  data/(model.json, build_report.log)
             render/ (git-ignored)  sheets/ (git-ignored)  KK01_แบบก่อสร้าง_ST00-ST18.pdf
  web/       HTML ออฟไลน์ ฉบับเต็ม + ฉบับส่งต่อ
<root>/เทียบ_BOQ_ผรม_กับโมเดล_<site>.xlsx
```
