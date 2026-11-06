# Parse the contractor BOQ PDF into rows (name, qty, unit, mat price, mat amt, lab price, lab amt, total) and check arithmetic.
import fitz, re, json, sys
src, out = sys.argv[1], sys.argv[2]
d = fitz.open(src)
num = lambda t: float(t.replace(",", "").replace("(", "-").replace(")", "")) if re.fullmatch(r"\(?[\d,]+(\.\d+)?\)?", t) else None
rows = []
for pi, p in enumerate(d):
    lines = {}
    for w in p.get_text("words"):
        lines.setdefault(round((w[1] + w[3]) / 6), []).append(w)
    for k in sorted(lines):
        ws = sorted(lines[k], key=lambda w: w[0])
        rows.append(dict(page=pi + 1, cells=[(round(w[0]), w[4]) for w in ws]))
with open(out, "w", encoding="utf-8") as f:
    for r in rows:
        f.write(f"p{r['page']} " + " | ".join(f"{x}:{t}" for x, t in r["cells"]) + "\n")

# ---- structured rows: column bands by x
BANDS = [("name", 0, 235), ("qty", 235, 258), ("unit", 258, 290), ("mp", 290, 335), ("ma", 335, 388), ("lp", 388, 425), ("la", 425, 470), ("tot", 470, 999)]
items = []
for r in rows:
    c = {}
    for x, t in r["cells"]:
        b = next(k for k, a, z in BANDS if a <= x < z)
        c[b] = (c.get(b, "") + " " + t).strip()
    nums = {k: num(c[k]) for k in ("qty", "mp", "ma", "lp", "la", "tot") if k in c and num(c[k]) is not None}
    if items and "name" not in c and nums:                      # continuation line
        items[-1].update({k: v for k, v in nums.items() if k not in items[-1] or items[-1][k] is None})
        continue
    if "name" in c and re.match(r"^\d+$", c["name"]) and False:
        pass
    items.append(dict(page=r["page"], name=c.get("name", ""), unit=c.get("unit", ""), **nums))
bad = []
for it in items:
    q = it.get("qty")
    for p_, a_ in (("mp", "ma"), ("lp", "la")):
        if q and it.get(p_) and it.get(a_) is not None and abs(q * it[p_] - it[a_]) > 0.6:
            bad.append((it["name"], q, it[p_], it[a_], q * it[p_]))
    if it.get("tot") is not None and (it.get("ma") or it.get("la")) and abs((it.get("ma") or 0) + (it.get("la") or 0) - it["tot"]) > 0.6:
        bad.append((it["name"], "sum", it.get("ma"), it.get("la"), it["tot"]))
json.dump(items, open(out.replace(".txt", ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=0)
with open(out.replace(".txt", "_bad.txt"), "w", encoding="utf-8") as f:
    for b in bad:
        f.write(repr(b) + "\n")
