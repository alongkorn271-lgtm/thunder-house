# Assemble index.html for the KK01 viewer: template + model.json + stage reports from the build log.
import json, os, re, sys
H = os.path.dirname(os.path.abspath(__file__))
LOG = sys.argv[1]
model = json.load(open(os.path.join(H, "model.json"), encoding="utf-8"))

# stage reports: the plain lines after the build banner, split at the first line of each stage
ANCH = [("ST01", "F1 ขุดดิน"), ("ST02", "P1 คอนกรีตตอม่อ"), ("ST03", "GB คอนกรีตคานคอดิน"), ("ST04", "PS แผ่นพื้น"),
        ("ST05", "C1 คอนกรีตเสา"), ("ST06", "ผนังก่ออิฐมอญ"), ("ST07", "ตะเข้สันเหล็ก"), ("ST08", "กระเบื้อง CPAC"),
        ("ST09", "ฝ้ายิปซัมบอร์ดธรรมดา"), ("ST11", "กระเบื้องพื้นผิวมัน"), ("ST10", "สีรองพื้นผนัง"),
        ("ST12a", "คอยล์ร้อนแอร์"), ("ST12b", "ท่ออ่อนลูกฟูก"), ("ST14", "ประตูไม้เนื้อแข็ง"),
        ("ST16", "ท่อน้ำดี PVC 13.5 ⌀1/2"), ("ST18", "ผนังแบบ 4")]
rep, cur = {}, None
for ln in open(LOG, encoding="utf-8", errors="replace").read().splitlines():
    if ln.startswith("Info: Saved"):
        break
    if ln.startswith("[") or not ln.strip():
        continue
    for k, a in ANCH:
        if ln.startswith(a):
            cur = k
    if cur and not ln.startswith("ยังไม่ได้ทำ (รอคำตอบ)"):
        rep.setdefault(cur, []).append(ln.strip())
assert len(rep) == len(ANCH), sorted(rep)
imgs = sorted((f for f in os.listdir(os.path.join(H, "img")) if f.endswith(".jpg")), key=lambda f: (f[:4], "overview" not in f, f))
tpl = open(os.path.join(H, "template.html"), encoding="utf-8").read()
blob = json.dumps(dict(model=model, rep=rep, imgs=imgs), ensure_ascii=False, separators=(",", ":"))
out = tpl.replace("/*__DATA__*/null", blob.replace("</", "<\\/"))
open(os.path.join(H, "index.html"), "w", encoding="utf-8").write(out)
print("index.html", os.path.getsize(os.path.join(H, "index.html")) // 1024, "KB;", sum(len(v) for v in rep.values()), "report lines;", len(imgs), "images")
