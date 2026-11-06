# -*- coding: utf-8 -*-
import math, base64, html, os

# ---- model & project are injected by the caller (see SKILL.md) ----
parts = []
PROJECT = dict(
    project=["ชื่อโครงการ", "บรรทัดที่ 2", "ขนาด ..."],
    owner=["เจ้าของงาน"],
    site=["สถานที่ก่อสร้าง"],
    contractor=["ผู้รับจ้าง", "อ้างอิงใบเสนอราคา ..."],
    revision="A   วันที่   แบบร่างเพื่อตรวจสอบ",
    status="(DRAFT — ห้ามใช้ก่อสร้างจนกว่าจะอนุมัติ)",
)
def set_model(model_parts):
    """Use the given part list for every View.draw_parts() call."""
    parts[:] = list(model_parts)
def set_project(**kw):
    PROJECT.update(kw)
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "fonts") + os.sep

PW, PH = 420.0, 297.0
FONT = "Plex, 'DejaVu Sans', sans-serif"

def esc(s): return html.escape(str(s), quote=True)
def f(v): return f"{v:.3f}".rstrip("0").rstrip(".")

# ---------------- material styles ----------------
def mat_class(p):
    m, g, i = p.get("mat", ""), p["g"], p["id"]
    if i.startswith("PED") or i.startswith("STEP"): return "conc"
    if "ISO" in m or g in ("walls", "ceiling") and "ISO" in p["name"]: return "iso"
    if i.startswith("MS-"): return "pu"
    if "Viva" in m: return "wood"
    if "Vinyl" in m: return "vinyl"
    if "กระจก" in m: return "glass"
    if i.startswith("CV-TOP") or "UPVC" in m and g == "cover": return "upvc"
    if g in ("base", "frame", "roofframe") or "เหล็ก" in m or i.startswith(("PLT", "TRM", "RB", "RP", "RT", "MB", "CRB", "FLS", "STP", "CV-WH", "RACK", "PIN", "GUT", "CV-FR", "CV-SK")):
        return "steel"
    return "equip"

TINT = dict(conc="#f1f0ec", iso="#ffffff", pu="#eef1f3", wood="#f6efe2", vinyl="#f4efe9", glass="#e3f1f6",
            upvc="#f7f9f7", steel="#e4e6e8", equip="#f2f2f2")
CUTFILL = dict(conc="url(#h-conc)", iso="url(#h-iso)", pu="url(#h-pu)", wood="url(#h-wood)", vinyl="#555",
               glass="#bfe0ea", upvc="#d9dfd9", steel="#1e1e1e", equip="#cfcfcf")

DEFS = """<defs>
<pattern id="h-conc" patternUnits="userSpaceOnUse" width="2.2" height="2.2"><rect width="2.2" height="2.2" fill="#e8e6df"/><circle cx="0.6" cy="0.7" r="0.18" fill="#555"/><circle cx="1.6" cy="1.7" r="0.12" fill="#555"/><path d="M1.4 0.3 l0.4 0.3 l-0.5 0.1z" fill="none" stroke="#666" stroke-width="0.08"/></pattern>
<pattern id="h-iso" patternUnits="userSpaceOnUse" width="1.6" height="1.6" patternTransform="rotate(45)"><rect width="1.6" height="1.6" fill="#fff"/><line x1="0" y1="0" x2="0" y2="1.6" stroke="#777" stroke-width="0.12"/><line x1="0" y1="0" x2="1.6" y2="0" stroke="#777" stroke-width="0.12"/></pattern>
<pattern id="h-pu" patternUnits="userSpaceOnUse" width="1.2" height="1.2" patternTransform="rotate(45)"><rect width="1.2" height="1.2" fill="#f4f6f7"/><line x1="0" y1="0" x2="0" y2="1.2" stroke="#6a7a86" stroke-width="0.12"/></pattern>
<pattern id="h-wood" patternUnits="userSpaceOnUse" width="1.5" height="1.5" patternTransform="rotate(-30)"><rect width="1.5" height="1.5" fill="#f3e7cf"/><line x1="0" y1="0" x2="0" y2="1.5" stroke="#8b6a3d" stroke-width="0.12"/></pattern>
<marker id="arr" viewBox="0 0 10 10" refX="10" refY="5" markerWidth="2.4" markerHeight="2.4" markerUnits="userSpaceOnUse" orient="auto-start-reverse"><path d="M0 1.5 L10 5 L0 8.5z" fill="#111"/></marker>
<marker id="dot" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="1.2" markerHeight="1.2" markerUnits="userSpaceOnUse"><circle cx="5" cy="5" r="5" fill="#111"/></marker>
</defs>"""

# ---------------- geometry ----------------
def halfs(p):
    if p["k"] == "box": return [s / 2 for s in p["s"]]
    r, h = p["r"], p["h"]
    return {"z": [r, r, h / 2], "x": [h / 2, r, r], "y": [r, h / 2, r]}[p["ax"]]

def rot(p, v):
    a = math.radians(p["rx"]); c, s = math.cos(a), math.sin(a)
    x, y, z = v
    return (x, y * c - z * s, y * s + z * c)

def corners(p, off=(0, 0, 0), hs=None):
    hx, hy, hz = hs or halfs(p)
    out = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                v = rot(p, (sx * hx, sy * hy, sz * hz))
                out.append((p["c"][0] + v[0] + off[0], p["c"][1] + v[1] + off[1], p["c"][2] + v[2] + off[2]))
    return out

EDGES = [(0, 1), (2, 3), (4, 5), (6, 7), (0, 2), (1, 3), (4, 6), (5, 7), (0, 4), (1, 5), (2, 6), (3, 7)]

def hull(pts):
    pts = sorted(set((round(a, 4), round(b, 4)) for a, b in pts))
    if len(pts) <= 2: return pts
    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for q in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], q) <= 0: lo.pop()
        lo.append(q)
    for q in reversed(pts):
        while len(up) >= 2 and cr(up[-2], up[-1], q) <= 0: up.pop()
        up.append(q)
    return lo[:-1] + up[:-1]

def long_axis(p):
    hs = halfs(p); return max(range(3), key=lambda i: hs[i])

# ---------------- view ----------------
AX = {"plan": 2, "front": 1, "back": 1, "left": 0, "right": 0}
SGN = {"plan": 1, "front": -1, "back": 1, "left": -1, "right": 1}   # nearness = SGN * coord

class View:
    def __init__(self, sheet, kind, scale, crop, at, plane=None, title=None, sub=None, clip=True, tdy=7, tdx=0):
        """crop=(u0,u1,v0,v1) world view coords; at=(px,py) paper pos of (u0,v0) (bottom-left)."""
        self.sh, self.kind, self.s, self.crop, self.at, self.plane, self.clip = sheet, kind, scale, crop, at, plane, clip
        self.out = []; self.ann = []; self.tdy = tdy; self.tdx = tdx
        self.cid = f"c{id(self)}"
        if title: self.sheet_title(title, sub)
    def uv(self, P):
        x, y, z = P
        return {"plan": (x, y), "front": (x, z), "back": (-x, z), "left": (-y, z), "right": (y, z)}[self.kind]
    def near(self, P): return SGN[self.kind] * P[AX[self.kind]]
    def pp(self, u, v):
        return (self.at[0] + (u - self.crop[0]) / self.s, self.at[1] - (v - self.crop[2]) / self.s)
    def P(self, P3): return self.pp(*self.uv(P3))
    def box_paper(self):
        x0, y1 = self.pp(self.crop[0], self.crop[2]); x1, y0 = self.pp(self.crop[1], self.crop[3])
        return x0, y0, x1, y1
    def sheet_title(self, title, sub):
        x0, y0, x1, y1 = self.box_paper()
        self.sh.label_title(x0 + self.tdx, y1 + self.tdy, title, sub)

    # ----- part drawing -----
    def _poly(self, pts_uv, fill, stroke, sw, extra=""):
        pts = " ".join(f"{f(a)},{f(b)}" for a, b in (self.pp(u, v) for u, v in pts_uv))
        return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" {extra}/>'

    def _circle_parallel(self, p):
        return p["k"] == "cyl" and abs(p["rx"]) < 0.01 and \
            {"z": 2, "x": 0, "y": 1}[p["ax"]] == AX[self.kind]

    def proj(self, p, off=(0, 0, 0)):
        if self._circle_parallel(p):
            u, v = self.uv((p["c"][0] + off[0], p["c"][1] + off[1], p["c"][2] + off[2]))
            return [(u + p["r"] * math.cos(t), v + p["r"] * math.sin(t)) for t in [i * math.pi / 18 for i in range(36)]]
        C = corners(p, off)
        if self.plane is not None:
            N0 = self.plane
            keep = [c for c in C if self.near(c) <= N0 + 1e-6]
            for a, b in EDGES:
                na, nb = self.near(C[a]), self.near(C[b])
                if (na - N0) * (nb - N0) < 0:
                    t = (N0 - na) / (nb - na)
                    keep.append(tuple(C[a][i] + t * (C[b][i] - C[a][i]) for i in range(3)))
            C = keep
        return hull([self.uv(c) for c in C])

    def section(self, p, hs=None):
        """cut face polygon (uv) of part p with plane, or None"""
        ax, N0 = AX[self.kind], self.plane
        W0 = N0 * SGN[self.kind]
        cx, cy, cz = p["c"]
        hx, hy, hz = hs or halfs(p)
        if p["k"] == "cyl":
            r, h, a = p["r"], p["h"], p["ax"]
            aidx = {"z": 2, "x": 0, "y": 1}[a]
            d = W0 - p["c"][ax]
            if aidx == ax:
                if abs(d) > h / 2: return None
                u, v = self.uv(p["c"]); return [(u + r * math.cos(t), v + r * math.sin(t)) for t in [i * math.pi / 18 for i in range(36)]]
            if abs(d) >= r: return None
            ch = math.sqrt(r * r - d * d)
            hh = [r, r, r]; hh[aidx] = h / 2
            for i in range(3):
                if i != aidx and i != ax: hh[i] = ch if False else hh[i]
            hh[ax] = 0
            # the remaining non-axis, non-plane dim keeps chord width
            other = [i for i in range(3) if i not in (aidx, ax)][0]
            hh[other] = ch
            pts = []
            for s1 in (-1, 1):
                for s2 in (-1, 1):
                    q = list(p["c"]); q[ax] = W0
                    q[aidx] += s1 * hh[aidx]; q[other] += s2 * hh[other]
                    pts.append(self.uv(q))
            return hull(pts)
        if ax == 0:
            if abs(W0 - cx) >= hx: return None
            pts = []
            for sy in (-1, 1):
                for sz in (-1, 1):
                    v = rot(p, (0, sy * hy, sz * hz)); pts.append(self.uv((W0, cy + v[1], cz + v[2])))
            return hull(pts)
        # plane along y or z: intersect rotated yz-rect with line
        rect = []
        for sy, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            v = rot(p, (0, sy * hy, sz * hz)); rect.append((cy + v[1], cz + v[2]))
        k = 0 if ax == 1 else 1      # coordinate index in (y,z) fixed by plane
        o = 1 - k
        vals = []
        for i in range(4):
            a, b = rect[i], rect[(i + 1) % 4]
            if (a[k] - W0) * (b[k] - W0) <= 0 and a[k] != b[k]:
                t = (W0 - a[k]) / (b[k] - a[k]); vals.append(a[o] + t * (b[o] - a[o]))
        if len(vals) < 2: return None
        lo, hi = min(vals), max(vals)
        pts = []
        for xx in (cx - hx, cx + hx):
            for ww in (lo, hi):
                q = [xx, 0, 0]; q[ax] = W0; q[1 + o] = ww
                pts.append(self.uv(q))
        return hull(pts)

    def draw_parts(self, pred=lambda p: True, cut=True, sw=0.13, color="#2b2b2b", tint=True, extra_parts=()):
        items = []
        for p in list(parts) + list(extra_parts):
            if not pred(p) or p["id"] in ("LD-BEAM",): continue
            C = corners(p)
            ns = [self.near(c) for c in C]
            if self.plane is not None and min(ns) > self.plane + 1e-6: continue
            poly = self.proj(p)
            if len(poly) < 3: continue
            depth = min(max(ns), self.plane) if self.plane is not None else max(ns)
            mc = mat_class(p)
            fill = TINT[mc] if tint else "#fff"
            op = ' fill-opacity="0.55"' if mc == "glass" else ""
            items.append((depth, sum(ns) / 8, self._poly(poly, fill, color, sw, op)))
        items.sort(key=lambda t: (t[0], t[1]))
        body = [t[2] for t in items]
        if self.plane is not None and cut:
            for p in parts:
                if not pred(p) or p["id"] == "LD-BEAM": continue
                sec = self.section(p)
                if not sec or len(sec) < 3: continue
                mc = mat_class(p)
                body.append(self._poly(sec, CUTFILL[mc], "#000", 0.3))
                if p.get("tube"):
                    la = long_axis(p); pa = AX[self.kind]
                    t = p["tube"]["t"]; hs = halfs(p)
                    if la == pa:
                        ih = [hs[i] - t if i != la else hs[i] for i in range(3)]
                    else:
                        d = abs(self.plane * SGN[self.kind] - p["c"][pa])
                        ih = None if d >= hs[pa] - t else [hs[i] - t if i not in (la, pa) else hs[i] for i in range(3)]
                        if ih: ih[la] = hs[la] - t
                    inner = self.section(p, ih) if ih else None
                    if inner and len(inner) >= 3: body.append(self._poly(inner, "#fff", "#000", 0.12))
        self.out += body

    def outline(self, p, off=(0, 0, 0), dash="1.2,0.8", sw=0.2, color="#444"):
        poly = self.proj(p, off) if self.plane is None else hull([self.uv(c) for c in corners(p, off)])
        self.out.append(self._poly(poly, "none", color, sw, f'stroke-dasharray="{dash}"'))

    # ----- annotations (paper level) -----
    def line(self, A, B, sw=0.18, dash=None, color="#111", world=True):
        a = self.P(A) if world else A; b = self.P(B) if world else B
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.ann.append(f'<line x1="{f(a[0])}" y1="{f(a[1])}" x2="{f(b[0])}" y2="{f(b[1])}" stroke="{color}" stroke-width="{sw}"{d}/>')
    def uvline(self, a, b, sw=0.18, dash=None, color="#111"):
        A, B = self.pp(*a), self.pp(*b)
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.ann.append(f'<line x1="{f(A[0])}" y1="{f(A[1])}" x2="{f(B[0])}" y2="{f(B[1])}" stroke="{color}" stroke-width="{sw}"{d}/>')
    def text_uv(self, u, v, s, size=2.2, anchor="middle", weight=400, color="#111", rot=0, dy=0):
        x, y = self.pp(u, v)
        self.ann.append(text(x, y + dy, s, size, anchor, weight, color, rot))

    def dim(self, a, b, off, txt=None, horiz=True, size=2.0, ext=True):
        """a,b in uv world; off paper mm (+ = up for horiz, + = right for vert)."""
        A, B = self.pp(*a), self.pp(*b)
        if horiz:
            y = min(A[1], B[1]) - off if off > 0 else max(A[1], B[1]) - off
            L = abs(b[0] - a[0]); x0, x1 = A[0], B[0]
            if ext:
                for X, Y in ((A[0], A[1]), (B[0], B[1])):
                    e = 1.2 if y < Y else -1.2
                    self.ann.append(f'<line x1="{f(X)}" y1="{f(Y - (0.8 if y < Y else -0.8))}" x2="{f(X)}" y2="{f(y - e)}" stroke="#333" stroke-width="0.1"/>')
            self.ann.append(f'<line x1="{f(x0 - 1)}" y1="{f(y)}" x2="{f(x1 + 1)}" y2="{f(y)}" stroke="#111" stroke-width="0.12"/>')
            for X in (x0, x1):
                self.ann.append(f'<line x1="{f(X - 0.7)}" y1="{f(y + 0.7)}" x2="{f(X + 0.7)}" y2="{f(y - 0.7)}" stroke="#111" stroke-width="0.3"/>')
            t = txt if txt is not None else f"{L:,.0f}"
            self.ann.append(text((x0 + x1) / 2, y - 0.8, t, size))
        else:
            x = max(A[0], B[0]) + off if off > 0 else min(A[0], B[0]) + off
            L = abs(b[1] - a[1]); y0, y1 = A[1], B[1]
            if ext:
                for X, Y in ((A[0], A[1]), (B[0], B[1])):
                    e = 1.2 if x > X else -1.2
                    self.ann.append(f'<line x1="{f(X + (0.8 if x > X else -0.8))}" y1="{f(Y)}" x2="{f(x + e)}" y2="{f(Y)}" stroke="#333" stroke-width="0.1"/>')
            self.ann.append(f'<line x1="{f(x)}" y1="{f(y0 + 1)}" x2="{f(x)}" y2="{f(y1 - 1)}" stroke="#111" stroke-width="0.12"/>')
            for Y in (y0, y1):
                self.ann.append(f'<line x1="{f(x - 0.7)}" y1="{f(Y + 0.7)}" x2="{f(x + 0.7)}" y2="{f(Y - 0.7)}" stroke="#111" stroke-width="0.3"/>')
            t = txt if txt is not None else f"{L:,.0f}"
            self.ann.append(text(x - 0.8, (y0 + y1) / 2, t, size, rot=-90))

    def chain(self, vals, v_or_u, off, horiz=True, size=1.9):
        for a, b in zip(vals[:-1], vals[1:]):
            if horiz: self.dim((a, v_or_u), (b, v_or_u), off, size=size, ext=False)
            else: self.dim((v_or_u, a), (v_or_u, b), off, horiz=False, size=size, ext=False)

    def leader(self, uvp, dx, dy, s, size=2.1, anchor=None, weight=400):
        x, y = self.pp(*uvp)
        tx, ty = x + dx, y + dy
        anchor = anchor or ("start" if dx >= 0 else "end")
        sx = tx + (2.5 if anchor == "start" else -2.5)
        self.ann.append(f'<polyline points="{f(x)},{f(y)} {f(tx)},{f(ty)} {f(sx)},{f(ty)}" fill="none" stroke="#111" stroke-width="0.14" marker-start="url(#dot)"/>')
        lines = s.split("\n")
        for i, ln in enumerate(lines):
            self.ann.append(text(sx + (0.6 if anchor == "start" else -0.6), ty + 0.75 + i * size * 1.25 - (len(lines) - 1) * size * 0.62, ln, size, anchor, weight))
    def call(self, uvp, tx, ty, s, size=2.1, anchor="start", elbow=None, weight=400):
        """leader from world uv point to absolute paper text position (tx,ty)"""
        x, y = self.pp(*uvp)
        ex = elbow if elbow is not None else (tx - 1.5 if anchor == "start" else tx + 1.5)
        pts = f"{f(x)},{f(y)} {f(ex)},{f(ty)} {f(tx - 0.5 if anchor == 'start' else tx + 0.5)},{f(ty)}"
        self.ann.append(f'<polyline points="{pts}" fill="none" stroke="#111" stroke-width="0.14" marker-start="url(#dot)"/>')
        lines = s.split("\n")
        for i, ln in enumerate(lines):
            self.ann.append(text(tx, ty + 0.75 + i * size * 1.3, ln, size, anchor, weight if i == 0 else 400))
    def wtext(self, P3, s, **kw):
        u, v = self.uv(P3); self.text_uv(u, v, s, **kw)

    def grid(self, name, val, horiz_line, ext=(0, 0), bubble="start"):
        """grid line: horiz_line False -> vertical line at u=val; True -> horizontal at v=val"""
        u0, u1, v0, v1 = self.crop
        if not horiz_line:
            a, b = self.pp(val, v0), self.pp(val, v1)
            ya, yb = a[1] + ext[0], b[1] - ext[1]
            self.ann.append(f'<line x1="{f(a[0])}" y1="{f(ya)}" x2="{f(a[0])}" y2="{f(yb)}" stroke="#666" stroke-width="0.12" stroke-dasharray="4,0.8,0.6,0.8"/>')
            self.ann.append(bubble_svg(a[0], ya + 2.6, name))
        else:
            a, b = self.pp(u0, val), self.pp(u1, val)
            xa = a[0] - ext[0]
            self.ann.append(f'<line x1="{f(xa)}" y1="{f(a[1])}" x2="{f(b[0] + ext[1])}" y2="{f(a[1])}" stroke="#666" stroke-width="0.12" stroke-dasharray="4,0.8,0.6,0.8"/>')
            self.ann.append(bubble_svg(xa - 2.6, a[1], name))

    def render(self):
        x0, y0, x1, y1 = self.box_paper()
        clip = f'<clipPath id="{self.cid}"><rect x="{f(x0)}" y="{f(y0)}" width="{f(x1 - x0)}" height="{f(y1 - y0)}"/></clipPath>'
        return clip, self.out

def bubble_svg(x, y, name):
    return f'<circle cx="{f(x)}" cy="{f(y)}" r="2.4" fill="#fff" stroke="#111" stroke-width="0.2"/>' + text(x, y + 0.75, name, 2.2, weight=600)

def text(x, y, s, size=2.2, anchor="middle", weight=400, color="#111", rot=0):
    tr = f' transform="rotate({rot} {f(x)} {f(y)})"' if rot else ""
    return f'<text x="{f(x)}" y="{f(y)}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{color}"{tr}>{esc(s)}</text>'

# ---------------- sheet ----------------
class Sheet:
    def __init__(self, no, title, scale_note, total):
        self.no, self.title, self.scale_note, self.total = no, title, scale_note, total
        self.views, self.raw = [], []
    def view(self, *a, **k):
        v = View(self, *a, **k); self.views.append(v); return v
    def add(self, s): self.raw.append(s)
    def label_title(self, x, y, title, sub=None):
        self.raw.append(text(x, y, title, 3.2, "start", 600))
        w = 3.2 * 0.55 * len(title)
        self.raw.append(f'<line x1="{f(x)}" y1="{f(y + 1.2)}" x2="{f(x + max(w, 40))}" y2="{f(y + 1.2)}" stroke="#111" stroke-width="0.35"/>')
        if sub: self.raw.append(text(x, y + 4.6, sub, 2.1, "start", 400, "#333"))
    def para(self, x, y, lines, size=2.2, lh=1.5, weight=400, color="#111", anchor="start"):
        for i, ln in enumerate(lines):
            if ln: self.raw.append(text(x, y + i * size * lh, ln, size, anchor, weight if not ln.startswith("§") else 600, color) if not ln.startswith("§") else text(x, y + i * size * lh, ln[1:], size + 0.3, anchor, 600, color))
        return y + len(lines) * size * lh
    def table(self, x, y, cols, rows, size=1.95, rh=4.0, head=True):
        tw = sum(c[1] for c in cols)
        out = []
        yy = y
        if head:
            out.append(f'<rect x="{f(x)}" y="{f(yy)}" width="{f(tw)}" height="{f(rh)}" fill="#e9ebe7" stroke="#111" stroke-width="0.15"/>')
            cx = x
            for name, w, *al in cols:
                out.append(text(cx + 1, yy + rh * 0.7, name, size, "start", 600)); cx += w
            yy += rh
        for r in rows:
            h = rh * max(1, max(len(str(c).split("\n")) for c in r))
            out.append(f'<rect x="{f(x)}" y="{f(yy)}" width="{f(tw)}" height="{f(h)}" fill="none" stroke="#111" stroke-width="0.1"/>')
            cx = x
            for (name, w, *al), c in zip(cols, r):
                a = al[0] if al else "start"
                for i, ln in enumerate(str(c).split("\n")):
                    px = cx + 1 if a == "start" else cx + w - 1
                    out.append(text(px, yy + rh * 0.7 + i * rh, ln, size, a))
                cx += w
            yy += h
        cx = x
        for name, w, *al in cols[:-1]:
            cx += w
            out.append(f'<line x1="{f(cx)}" y1="{f(y)}" x2="{f(cx)}" y2="{f(yy)}" stroke="#111" stroke-width="0.1"/>')
        self.raw += out
        return yy

    def titleblock(self):
        o = []
        o.append('<rect x="8" y="8" width="404" height="281" fill="none" stroke="#111" stroke-width="0.6"/>')
        X = 352
        o.append(f'<line x1="{X}" y1="8" x2="{X}" y2="289" stroke="#111" stroke-width="0.4"/>')
        rows = [("โครงการ", PROJECT["project"], 22), ("เจ้าของงาน", PROJECT["owner"], 15),
                ("สถานที่ก่อสร้าง", PROJECT["site"], 15), ("ผู้รับจ้าง", PROJECT["contractor"], 15)]
        y = 8
        for lab, lines, h in rows:
            o.append(text(X + 2, y + 3.6, lab, 1.8, "start", 400, "#555"))
            for i, ln in enumerate(lines): o.append(text(X + 2, y + 7.6 + i * 3.4, ln, 2.15, "start", 600 if i == 0 else 400))
            y += h
            o.append(f'<line x1="{X}" y1="{f(y)}" x2="412" y2="{f(y)}" stroke="#111" stroke-width="0.25"/>')
        # revision
        o.append(text(X + 2, y + 3.6, "แก้ไขครั้งที่", 1.8, "start", 400, "#555"))
        o.append(text(X + 2, y + 8, PROJECT["revision"], 2.0, "start"))
        o.append(text(X + 2, y + 11.8, PROJECT["status"], 1.8, "start", 600, "#a33"))
        y += 16
        o.append(f'<line x1="{X}" y1="{f(y)}" x2="412" y2="{f(y)}" stroke="#111" stroke-width="0.25"/>')
        for lab in ("ออกแบบ/เขียนแบบ", "ตรวจสอบ", "อนุมัติ"):
            o.append(text(X + 2, y + 3.6, lab, 1.8, "start", 400, "#555"))
            o.append(f'<line x1="{X + 2}" y1="{f(y + 9)}" x2="{X + 40}" y2="{f(y + 9)}" stroke="#999" stroke-width="0.12" stroke-dasharray="0.6,0.6"/>')
            o.append(text(X + 42, y + 3.6, "วันที่", 1.8, "start", 400, "#555"))
            y += 11
            o.append(f'<line x1="{X}" y1="{f(y)}" x2="412" y2="{f(y)}" stroke="#111" stroke-width="0.15"/>')
        o.append(f'<line x1="{X}" y1="{f(y)}" x2="412" y2="{f(y)}" stroke="#111" stroke-width="0.25"/>')
        # sheet title area
        o.append(text(X + 2, y + 3.6, "ชื่อแบบ", 1.8, "start", 400, "#555"))
        for i, ln in enumerate(self.title.split("\n")):
            o.append(text(X + 2, y + 9 + i * 4.6, ln, 3.0, "start", 600))
        y2 = 289 - 34
        o.append(f'<line x1="{X}" y1="{y2}" x2="412" y2="{y2}" stroke="#111" stroke-width="0.25"/>')
        o.append(text(X + 2, y2 + 3.6, "มาตราส่วน", 1.8, "start", 400, "#555"))
        o.append(text(X + 2, y2 + 8, self.scale_note, 2.1, "start", 600))
        o.append(text(X + 2, y2 + 12.5, "หน่วย: มิลลิเมตร (ยกเว้นระบุ)", 1.8, "start", 400, "#333"))
        o.append(f'<line x1="{X}" y1="{y2 + 15}" x2="412" y2="{y2 + 15}" stroke="#111" stroke-width="0.25"/>')
        o.append(text(X + 2, y2 + 18.6, "แผ่นที่", 1.8, "start", 400, "#555"))
        o.append(text(X + 30, y2 + 30, self.no, 9, "middle", 700))
        o.append(text(X + 57, y2 + 30, f"/{self.total}", 2.4, "end", 400, "#444"))
        return o

    def svg(self):
        clips, body = [], []
        for v in self.views:
            c, b = v.render(); clips.append(c)
            body.append((f'<g clip-path="url(#{v.cid})">' if v.clip else '<g>') + "".join(b) + "</g>" + "".join(v.ann))
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{PW}mm" height="{PH}mm" viewBox="0 0 {PW} {PH}" font-family="{FONT}">'
                + DEFS.replace("</defs>", "".join(clips) + "</defs>") + '<rect width="420" height="297" fill="#fff"/>'
                + "".join(body) + "".join(self.raw) + "".join(self.titleblock()) + "</svg>")

def annot_layer(v):
    """call to mark where clipped drawing ends and unclipped annotation begins"""
    v._nclip = len(v.out)

def page_html(sheets, fontdir=FONT_DIR):
    def b64(fn): return base64.b64encode(open(fontdir + fn, "rb").read()).decode()
    ff = ""
    for w in (400, 600):
        ff += f"@font-face{{font-family:Plex;font-weight:{w};src:url(data:font/woff2;base64,{b64(f'ibm-plex-sans-thai-thai-{w}-normal.woff2')}) format('woff2');unicode-range:U+0E01-0E5B,U+200C-200D,U+25CC}}"
        ff += f"@font-face{{font-family:Plex;font-weight:{w};src:url(data:font/woff2;base64,{b64(f'ibm-plex-sans-thai-latin-{w}-normal.woff2')}) format('woff2');unicode-range:U+0000-00FF,U+2000-206F,U+2212}}"
    pages = "".join(f'<div class="pg">{s.svg()}</div>' for s in sheets)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{ff}
@page{{size:420mm 297mm;margin:0}}html,body{{margin:0;padding:0}}.pg{{width:420mm;height:297mm;page-break-after:always;overflow:hidden}}
.pg:last-child{{page-break-after:auto}}svg{{display:block}}</style></head><body>{pages}</body></html>"""
