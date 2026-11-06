# HTML sheets -> A3 PDF + PNG previews with headless Chrome (shapes Thai correctly).
#     python render_pdf.py            (uses sheets/KK01_ST00-ST18.html and sheets/_ST-xx.html)
import glob, os, subprocess, sys
H = os.path.dirname(os.path.abspath(__file__))
S = os.path.join(H, "sheets")
CHROME = next(p for p in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe") if os.path.exists(p))
url = lambda p: "file:///" + os.path.abspath(p).replace("\\", "/")
base = [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars", "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=4000"]
pdf = os.path.join(H, "KK01_แบบก่อสร้าง_ST00-ST18.pdf")
subprocess.run(base + ["--no-pdf-header-footer", f"--print-to-pdf={pdf}", url(os.path.join(S, "KK01_ST00-ST18.html"))],
               check=True, capture_output=True)
import fitz                                      # Chrome writes uncompressed streams: recompress (68 MB -> ~4 MB)
_d = fitz.open(pdf); _d.save(pdf + ".tmp", garbage=4, deflate=True, deflate_images=True); _d.close()
os.replace(pdf + ".tmp", pdf)
print("PDF", pdf, os.path.getsize(pdf) // 1024, "KB")
os.makedirs(os.path.join(S, "png"), exist_ok=True)
only = sys.argv[1:]
for f in sorted(glob.glob(os.path.join(S, "_ST-*.html"))):
    n = os.path.basename(f)[1:-5]
    if only and n not in only:
        continue
    out = os.path.join(S, "png", n + ".png")
    subprocess.run(base + ["--force-device-scale-factor=1.5", "--window-size=1588,1123", f"--screenshot={out}", url(f)],
                   check=True, capture_output=True)
    print("PNG", out)
