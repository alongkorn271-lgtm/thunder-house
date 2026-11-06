# Single-file offline copies of the viewer: images inlined as data URIs; the "share" copy drops the negotiation tab.
import base64, os, re, sys
H = os.path.dirname(os.path.abspath(__file__))
OUTDIR = sys.argv[1]
src = open(os.path.join(H, "index.html"), encoding="utf-8").read()
imgs = {f: "data:image/jpeg;base64," + base64.b64encode(open(os.path.join(H, "img", f), "rb").read()).decode()
        for f in os.listdir(os.path.join(H, "img")) if f.endswith(".jpg")}
inl = "const IMGDATA = " + __import__("json").dumps(imgs) + ";\n"
full = src.replace("const KK = ", inl + "const KK = ", 1)
assert 'src="img/${f}"' in full
full = full.replace('src="img/${f}"', 'src="${IMGDATA[f] || "img/" + f}"')


def strip_neg(s):
    s = re.sub(r'\s*<button role="tab" aria-selected="false" data-tab="neg">ต่อรอง</button>', "", s)
    a = s.index('<div class="pane" id="p-neg">')
    b = s.index('<div class="pane" id="p-check">')
    s = s[:a] + s[b:]
    s = s.replace("boqTable(); negTab();", "boqTable();")
    a = s.index("/* negotiation:")
    b = s.index("function negTab(){")
    s = s[:a] + "const NEG = null;\n" + s[b:]
    return s


share = strip_neg(full)
for name, body in (("KK01_บ้านเกาะคา_3D_ฉบับเต็ม.html", full), ("KK01_บ้านเกาะคา_3D_ส่งต่อ.html", share)):
    p = os.path.join(OUTDIR, name)
    open(p, "w", encoding="utf-8").write(body)
    print(name, os.path.getsize(p) // 1024, "KB")
