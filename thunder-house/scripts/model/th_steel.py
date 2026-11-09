# -*- coding: utf-8 -*-
"""Cold-formed steel sections for the roof frame (thunder-house, own implementation).

Section outlines live in a local (s, z) plane: s across the section, z up. A member is swept along u by
`place(u, s, z) -> (x, y, z)`. Lengths in metres.

  lipped_c(h, b, c, t)   lipped channel: web at s = 0 (z 0…h), flanges to s = b, lips turn inward at s = b
                         (two of them toe to toe = the "2C" closed box used for wall plates, ridges, hips)
  box_tube(B, H, t)      square / rectangular hollow section, centred on s = 0, z 0…H → (outer, inner) loops
  area / tube_area       cross-section area (m²) → kg/m with RHO
  prism / tube           sweep an outline / a hollow loop pair into a bmesh as one closed solid
  obb / obb_overlap      oriented box of a straight member and the penetration depth of two boxes (clash check)
"""
import math
import bmesh
from mathutils import Vector

RHO = 7850.0  # kg/m³ steel


def _arc(cs, cz, r, a0, a1, n):
    return [(cs + r * math.cos(math.radians(a0 + (a1 - a0) * k / n)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * k / n))) for k in range(n + 1)]


def lipped_c(h, b, c, t, ri=None, n=8):
    """Closed outline: the outer face from the bottom lip tip round to the top lip tip, then the inner face back.
    Every bend has inner radius ri (default t); outer and inner faces have the same point count."""
    ri = t if ri is None else ri
    ro = ri + t
    outer = ([(b, c)] + _arc(b - ro, ro, ro, 0, -90, n) + _arc(ro, ro, ro, -90, -180, n)
             + _arc(ro, h - ro, ro, 180, 90, n) + _arc(b - ro, h - ro, ro, 90, 0, n) + [(b, h - c)])
    inner = ([(b - t, h - c)] + _arc(b - ro, h - ro, ri, 0, 90, n) + _arc(ro, h - ro, ri, 90, 180, n)
             + _arc(ro, ro, ri, 180, 270, n) + _arc(b - ro, ro, ri, 270, 360, n) + [(b - t, c)])
    return outer + inner


def area(poly):
    """Shoelace area of a closed outline (always positive)."""
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))) / 2


def _rounded_rect(B, H, r, off, n):
    """Rectangle B × H centred on s = 0, z 0…H, shrunk by `off` on every side, corner radius r."""
    s0, s1, z0, z1 = -B / 2 + off, B / 2 - off, off, H - off
    return (_arc(s1 - r, z0 + r, r, -90, 0, n) + _arc(s1 - r, z1 - r, r, 0, 90, n)
            + _arc(s0 + r, z1 - r, r, 90, 180, n) + _arc(s0 + r, z0 + r, r, 180, 270, n))


def box_tube(B, H, t, ro=None, n=6):
    """(outer, inner) loops of a hollow section B × H × t; outer corner radius ro (default 2t), inner ro − t."""
    ro = 2 * t if ro is None else ro
    return _rounded_rect(B, H, ro, 0.0, n), _rounded_rect(B, H, max(ro - t, 1e-5), t, n)


def tube_area(outer, inner):
    return area(outer) - area(inner)


def _ring(bm, pts, u, place):
    return [bm.verts.new(place(u, s, z)) for s, z in pts]


def _finish(bm, faces):
    bmesh.ops.recalc_face_normals(bm, faces=faces)


def prism(bm, poly, u0, u1, place):
    """Sweep a strip outline (outer face + inner face, as lipped_c returns) from u0 to u1 as one closed solid.
    Side walls follow the whole loop; each end cap is a row of quads pairing the outer and inner faces."""
    k = len(poly) // 2
    a, b = _ring(bm, poly, u0, place), _ring(bm, poly, u1, place)
    m = len(poly)
    faces = [bm.faces.new((a[i], a[(i + 1) % m], b[(i + 1) % m], b[i])) for i in range(m)]
    for ring in (a, b):
        o, r = ring[:k], ring[k:][::-1]
        faces += [bm.faces.new((o[i], o[i + 1], r[i + 1], r[i])) for i in range(k - 1)]
    _finish(bm, faces)
    return faces


def tube(bm, outer, inner, u0, u1, place):
    """Sweep a hollow section (outer and inner loops of equal length) from u0 to u1 as one closed solid."""
    m = len(outer)
    oa, ob = _ring(bm, outer, u0, place), _ring(bm, outer, u1, place)
    ia, ib = _ring(bm, inner, u0, place), _ring(bm, inner, u1, place)
    faces = []
    for p, q in ((oa, ob), (ia, ib)):
        faces += [bm.faces.new((p[i], p[(i + 1) % m], q[(i + 1) % m], q[i])) for i in range(m)]
    for o, r in ((oa, ia), (ob, ib)):
        faces += [bm.faces.new((o[i], o[(i + 1) % m], r[(i + 1) % m], r[i])) for i in range(m)]
    _finish(bm, faces)
    return faces


def _hull(pts):
    pts = sorted(set((round(x, 9), round(y, 9)) for x, y in pts))
    if len(pts) <= 2:
        return pts
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def obb(verts, d):
    """Tightest box round a straight member's vertices with one axis along d → (centre, [d, e1, e2], half sizes).
    The two cross axes come from the smallest-area rectangle round the section's convex hull."""
    d = Vector(d).normalized()
    a = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0))
    e1 = d.cross(a).normalized()
    e2 = d.cross(e1).normalized()
    hull = _hull([(v.dot(e1), v.dot(e2)) for v in verts])
    best = None
    for i in range(len(hull)):
        p, q = hull[i], hull[(i + 1) % len(hull)]
        ex, ey = q[0] - p[0], q[1] - p[1]
        L = math.hypot(ex, ey)
        if L < 1e-12:
            continue
        ux, uy = ex / L, ey / L
        a1 = [x * ux + y * uy for x, y in hull]
        a2 = [-x * uy + y * ux for x, y in hull]
        ar = (max(a1) - min(a1)) * (max(a2) - min(a2))
        if best is None or ar < best[0]:
            best = (ar, ux, uy, min(a1), max(a1), min(a2), max(a2))
    if best is None:
        best = (0, 1.0, 0.0, 0, 0, 0, 0)
    _, ux, uy, l1, h1, l2, h2 = best
    f1 = (e1 * ux + e2 * uy).normalized()
    f2 = (e1 * -uy + e2 * ux).normalized()
    ds = [v.dot(d) for v in verts]
    c = d * ((min(ds) + max(ds)) / 2) + f1 * ((l1 + h1) / 2) + f2 * ((l2 + h2) / 2)
    return c, [d, f1, f2], [(max(ds) - min(ds)) / 2, (h1 - l1) / 2, (h2 - l2) / 2]


def obb_overlap(A, B):
    """Penetration depth of two oriented boxes by the separating-axis test over 15 axes (the smallest overlap
    found); a value ≤ 0 means the boxes are apart or only touching."""
    ca, aa, ha = A
    cb, ab, hb = B
    t = Vector(cb) - Vector(ca)
    axes = list(aa) + list(ab) + [x.cross(y) for x in aa for y in ab]
    depth = math.inf
    for ax in axes:
        if ax.length < 1e-9:
            continue
        n = ax.normalized()
        ra = sum(h * abs(n.dot(v)) for h, v in zip(ha, aa))
        rb = sum(h * abs(n.dot(v)) for h, v in zip(hb, ab))
        dep = ra + rb - abs(t.dot(n))
        if dep <= 0:
            return dep
        depth = min(depth, dep)
    return depth


def selftest():
    """Areas against the TIS / JIS tables (rounded bends): C100×50×20×2.3 ≈ 4.06 kg/m, 50×50×2.0 tube ≈ 2.9 kg/m."""
    c = area(lipped_c(0.100, 0.050, 0.020, 0.0023)) * RHO
    o, i = box_tube(0.050, 0.050, 0.002, ro=0.006, n=32)
    s = tube_area(o, i) * RHO
    assert 3.9 < c < 4.2, f"C100 {c:.3f} kg/m"
    assert 2.8 < s < 3.0, f"tube 50x50x2 {s:.3f} kg/m"
    a = (Vector((0, 0, 0)), [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))], [1, 1, 1])
    b = (Vector((1.5, 0, 0)), [Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))], [1, 1, 1])
    assert abs(obb_overlap(a, b) - 0.5) < 1e-9
    return round(c, 3), round(s, 3)
