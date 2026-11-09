"""KK01 ST12b ไฟฟ้า – วงจร ท่อ สาย (generic ST12) – exec'd after kk01_elec.py, built after ST12a.

The user (5 พ.ย. 69): system / grade / consumer unit from the contractor's BOQ — Schneider Square D Classic consumer
unit, Schneider AvatarOn switches and sockets, THW in PVC conduit (EE-01 "ร้อยท่อ ⌀PVC ในผนังและบนฝ้าเพดาน"),
2×4 boxes, ground rod 5/8" × 8 ft + 10 sq.mm; AC sized from the rooms (ST12a EL_BTU); water heaters, exhaust fans
(none: the contractor dropped them) and meter as recommended.
Wire sizes EE-01: lighting 2.5, sockets 2.5, small AC 4.0; water heater 4.0 (4,500 W, 20 A); main THW 16 + earth 10.
Routing (designer's rules for this house, after common practice):
  - one PVC 20 mm (1/2") conduit per circuit, rigid, bent at r ≥ 102 mm (no elbows); the main 32 mm (1") r ≥ 146;
  - over the ceilings each circuit has its own height lane (main house 3.76 + 0.022 k, under the lean-to 3.15), so
    circuits cross without touching; runs stay ≥ 0.20 m off the walls, orthogonal, a 4×4 box at every branch and over
    every downlight (fixed to a hanger), flex from that box into the light through its cut-out;
  - a wall is crossed square through brick (never a tie column, a column or an opening); into the lean-to (ceiling
    +3.10) a run goes down a chase on the house face and bends through wall C at 3.15;
  - a wall device: the run comes square to the wall at its position and bends down into a chase (centre on the brick
    face, under the plaster) onto the box; a device on the far face of a wall with no void in front (outside, the
    laundry, the verandahs on wall C) is reached from the room behind: chase down, an S through the brick, chase down
    the far face; chases may cross the mid-height bands (ทับหลังกลางผนัง), never a tie column;
  - each circuit leaves the consumer unit in its own chase (25 mm apart) up into the living-room void.
Wire per piece: lighting L + N + E + switched line (4), switch drops 2, light flex 3; sockets / AC / heater 3;
+ 0.15 m slack at every end (earlier jobs). Objects (collection "KK01 ST12b Conduit"): CD_<circuit> (rigid),
CD_<circuit>_Flex, CD_Boxes (4×4), CD_MAIN, EL_METER. Spec: ST12_elec_spec.md.
"""

from mathutils import Vector

EC = dict(r=0.102, r_main=0.146, od=0.020, od_main=0.032, lane0=3.76, lane_s=0.022, lane_main=4.12, lt_z=3.15,
          off=0.25, jb=(0.115, 0.115, 0.055), slot=0.025, s_v=0.20, stock=4.0, clip=0.90, slack=0.15,
          meter=(4.30, -0.30, 1.80), rod="หลักดิน 5/8\" × 8 ฟุต + สายดิน THW 10 sq.mm")
# (name, breaker, wire sq.mm, RCBO, lane index, devices by ST12a object name)
CIRCUITS = [
    ("L1", "16 A", 2.5, False, ["DL:bed1", "DL:dressing", "DL:corridor", "DL:bath1", "DL:storage", "EL_SW_00", "EL_SW_01", "EL_SW_02", "EL_SW_03"]),
    ("L2", "16 A", 2.5, False, ["DL:living", "DL:verandah_front", "DL:verandah_rear", "DL:kitchen", "EAVE", "EL_FLUO",
                                "EL_SW_04", "EL_SW_05", "EL_SW_06", "EL_SW_08"]),
    ("L3", "16 A", 2.5, False, ["DL:bed2", "DL:bath2", "DL:bed3", "EL_SW_07", "EL_SW_09", "EL_SW_10"]),
    ("P1", "16 A", 2.5, False, [f"EL_SO_{i:02d}" for i in (4, 5, 6, 7, 10, 11, 12)]),
    ("P2", "16 A", 2.5, False, [f"EL_SO_{i:02d}" for i in (14, 15, 16, 18, 20, 21, 22)]),
    ("P3", "16 A", 2.5, False, [f"EL_SO_{i:02d}" for i in (9, 17, 19, 23, 24)]),
    ("P4", "16 A", 2.5, False, [f"EL_SO_{i:02d}" for i in (25, 27, 28, 29)]),
    ("P5", "16 A", 2.5, True, [f"EL_SO_{i:02d}" for i in (0, 1, 2, 3, 8, 13)]),
    ("P6", "16 A", 2.5, True, [f"EL_SO_{i:02d}" for i in (26, 30, 31, 32, 33)]),
    ("AC1", "20 A", 4.0, False, ["EL_FCU_bed1"]),
    ("AC2", "20 A", 4.0, False, ["EL_FCU_bed2"]),
    ("AC3", "20 A", 4.0, False, ["EL_FCU_bed3"]),
    ("WH1", "20 A", 4.0, True, ["EL_WH_1"]),
    ("WH2", "20 A", 4.0, True, ["EL_WH_2"]),
]
LEANTO_ROOMS = ("kitchen", "verandah_rear")
WEST = ("L1", "P1", "P5", "AC1", "WH1")                 # leave the CU straight through its wall into bed 1
C_COND = "KK01 ST12b Conduit"
STAGES.append(C_COND)


# ---------------------------------------------------------------- the voids and the walls between them

def _cd_rooms():
    """{room: dict(rect, level, zone)} — ceiling voids: rooms (3.60), lean-to rooms (3.10), eave / front verandah."""
    out = {}
    for n, (lvl, tp, pcs, rr) in _ceiling_rooms().items():
        zone = "lt" if n in LEANTO_ROOMS else "eave" if n == "verandah_front" else "main"
        out[n] = dict(rect=rr, level=lvl, zone=zone)
    eave, _ = _soffit_pieces()
    for i, p in enumerate(eave):
        out[f"eave_{i}"] = dict(rect=p, level=_soffit_level(), zone="eave")
    return out


def _cd_links(rooms):
    """[(a, b, kind, ax, plane, lo, hi)] — open (rects touch / overlap) or wall (gap 5–30 cm): ax = wall normal axis,
    plane = the wall's mid line, lo..hi = the shared stretch less 0.15 at each end."""
    names = sorted(rooms)
    out = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            ra, rb = rooms[a]["rect"], rooms[b]["rect"]
            ov = [min(ra[k + 2], rb[k + 2]) - max(ra[k], rb[k]) for k in (0, 1)]
            if ov[0] > -0.01 and ov[1] > -0.01 and max(ov) > 0.30:
                out.append((a, b, "open", None, None, None, None))
                continue
            if rooms[a]["zone"] == "eave" and rooms[b]["zone"] == "eave":
                continue                                       # soffit pieces: only where they touch
            for ax in (0, 1):
                o = 1 - ax
                if ov[o] < 0.30:
                    continue
                for p, q in ((ra, rb), (rb, ra)):
                    g = q[ax] - p[ax + 2]
                    if 0.05 < g < 0.30:
                        lo, hi = max(ra[o], rb[o]) + 0.15, min(ra[o + 2], rb[o + 2]) - 0.15
                        if hi > lo:
                            # the wall's real centre: its brick in the gap (rooms are traced at the ceiling, wall B's
                            # kitchen side stops at the lean-to steel)
                            br = [w for w in _cd_brick_boxes() if w[ax] >= p[ax + 2] - 0.02 and w[ax + 3] <= q[ax] + 0.02 and
                                  w[o] < hi and w[o + 3] > lo and (w[ax + 3] - w[ax]) < 0.12]
                            pl = (min(w[ax] for w in br) + max(w[ax + 3] for w in br)) / 2 if br else (p[ax + 2] + q[ax]) / 2
                            out.append((a, b, "wall", ax, pl, lo, hi))
    return out


def _cd_hard():
    """Ties (vertical), columns, openings: a conduit never passes through them (bands and lintels may be chased)."""
    out = []
    for (el, _), x in qto(C_WALL).items():
        for b in x["boxes"]:
            if el == "opening" or (el == "concrete" and (b[5] - b[2]) > max(b[3] - b[0], b[4] - b[1])):
                out.append(b)
    out += [b for (el, _), x in qto(C_COL).items() if el == "concrete" for b in x["boxes"]]
    return out


def _cd_line_clear(hard, p, q, rad):
    """Segment p→q (3D) keeps rad off every hard box (sampled every 1 cm)."""
    n = max(2, int(math.dist(p, q) / 0.01) + 1)
    for i in range(n):
        t = i / (n - 1)
        c = [p[k] + (q[k] - p[k]) * t for k in range(3)]
        for b in hard:
            if all(b[k] - rad < c[k] < b[k + 3] + rad for k in range(3)):
                return False
    return True


# ---------------------------------------------------------------- geometry helpers

def _fillet(pts, r, step=0.015):
    """Sharp polyline → arcs of radius r at every corner (tangent length clamped to half of each leg): samples."""
    if len(pts) < 3:
        return [tuple(p) for p in pts]
    V = [Vector(p) for p in pts]
    out = [V[0]]
    for i in range(1, len(V) - 1):
        a, b, c = V[i - 1], V[i], V[i + 1]
        u, w = (a - b), (c - b)
        if u.length < 1e-9 or w.length < 1e-9:
            continue
        u.normalize()
        w.normalize()
        th = math.pi - u.angle(w)                         # turn angle
        if th < 1e-4:
            out.append(b)
            continue
        t = r * math.tan(th / 2)
        t = min(t, (b - a).length / 2 if i > 1 else (b - a).length, (c - b).length / 2 if i < len(V) - 2 else (c - b).length)
        p0, p1 = b + u * t, b + w * t
        re = t / math.tan(th / 2)
        bis = (u + w).normalized()
        cen = b + bis * (re / math.cos(th / 2) if math.cos(th / 2) > 1e-9 else 0)
        n = max(2, int(re * th / step) + 1)
        v0, v1 = p0 - cen, p1 - cen
        for k in range(n + 1):
            s = k / n
            ang = th * s
            # slerp between v0 and v1 about the centre
            om = v0.angle(v1)
            if om < 1e-9:
                pt = p0
            else:
                pt = cen + (v0 * math.sin((1 - s) * om) + v1 * math.sin(s * om)) / math.sin(om)
            out.append(pt)
    out.append(V[-1])
    clean = [out[0]]
    for p in out[1:]:
        if (p - clean[-1]).length > 1e-6:
            clean.append(p)
    return [tuple(p) for p in clean]


def _cd_in(rect, p, m=0.0):
    return rect[0] + m - 1e-9 <= p[0] <= rect[2] - m + 1e-9 and rect[1] + m - 1e-9 <= p[1] <= rect[3] - m + 1e-9


def _cd_room_at(rooms, p, m=0.0, zones=None):
    best = None
    for n, d in rooms.items():
        if (zones is None or d["zone"] in zones) and _cd_in(d["rect"], p, m):
            r = d["rect"]
            dist = max(r[0] - p[0], 0, p[0] - r[2]) + max(r[1] - p[1], 0, p[1] - r[3])
            if best is None or dist < best[0]:
                best = (dist, n)
    return best[1] if best else None


LT_LANE = {"L2": 3.21}


def _cd_lane_min(zone):
    return EC["lt_z"] if zone == "lt" else EC["lane0"]                                 # under the lean-to: P3 at the hole height 3.15, L2 above it


def _cd_lane(c, zone):
    k = [x[0] for x in CIRCUITS].index(c)
    return LT_LANE.get(c, EC["lt_z"]) if zone == "lt" else EC["lane0"] + EC["lane_s"] * k


# ---------------------------------------------------------------- devices → attach geometry

def _cd_devices():
    """{name: dict(kind, room, approach (x, y), tail [sharp 3D points from the approach point on to the device])}."""
    rooms = _cd_rooms()
    objs = {o.name: o for o in _coll(C_ELEC).objects}
    walls = _obstacles()
    out = {}
    for n, o in objs.items():
        if not o.data or o.data.get("element") != "elec":
            continue
        dt = o.data["type"]
        b = _el_bounds(o)
        c = [(b[k] + b[k + 3]) / 2 for k in range(3)]
        if dt in ("downlight", "eave"):
            room = _cd_room_at(rooms, c, 0.0)
            out[n] = dict(kind="light", room=room, at=(c[0], c[1]), top=b[5])
            continue
        if dt not in ("switch", "socket", "socket_wp", "fluo", "fcu", "wh"):
            continue
        ax, sg = o.data["ax"], o.data["sg"]
        face = b[ax] if sg > 0 else b[ax + 3]                  # plate back = the finished face
        u = c[1 - ax]
        # the brick face behind the finish: walk back through finishes + plaster to the first brick / tie / column
        P = [c[0], c[1], c[2]]
        brick = None
        for k in range(1, 80):
            P[ax] = face - sg * k * 0.001
            hit = [q for q in _cd_brick_boxes() if q[0] <= P[0] <= q[3] and q[1] <= P[1] <= q[4] and q[2] <= P[2] <= q[5]]
            if hit:
                brick = hit[0][ax + 3] if sg > 0 else hit[0][ax]      # the face itself
                break
        assert brick is not None, f"[chase] {n}: no brick behind it"
        wall_t = BRICK["t"]
        top = b[5] if dt != "fcu" else b[5]
        box_top = (c[2] + 0.0575) if dt in ("switch",) else (c[2] + 0.034) if dt != "fcu" else b[5]
        front = [c[0], c[1]]
        front[ax] = face + sg * (EC["off"] + 0.05)
        room = _cd_room_at(rooms, front, 0.0)
        behind = [c[0], c[1]]
        behind[ax] = brick - sg * (wall_t + 0.03 + EC["off"] + 0.05)
        rb = _cd_room_at(rooms, behind, 0.0)
        if room is not None and rooms[room]["zone"] in ("lt", "eave") and rb is not None and rooms[rb]["zone"] == "main":
            room = None                                        # outside / lean-to face of a house wall: from the house side
        thr = None
        far = brick - sg * wall_t
        back = [c[0], c[1]]
        back[ax] = far - sg * (0.03 + EC["off"] + 0.05)
        rbk = _cd_room_at(rooms, back, 0.0)
        if rbk:
            apb = [c[0], c[1]]
            apb[ax] = far - sg * (0.015 + EC["off"])
            zs_ = min(rooms[rbk]["level"] - 0.08, _cd_lane_min(rooms[rbk]["zone"]) - 0.25)
            thr = dict(kind="through", room=rbk, ax=ax, sg=-sg, u=u, approach=tuple(apb), brick=brick, far=far,
                       tail=lambda z, ap=apb, far=far, brick=brick, ax=ax, u=u, bt=box_top, zs=zs_: [
                           _p3(ax, ap[ax], u, z), _p3(ax, far, u, z), _p3(ax, far, u, zs), _p3(ax, brick, u, zs - EC["s_v"]), _p3(ax, brick, u, bt)])
        if room is not None and dt != "fluo" and not (n in _CD_FORCE_THROUGH):
            ap = [c[0], c[1]]
            ap[ax] = brick + sg * (0.015 + EC["off"])
            tail = lambda z, ap=ap, brick=brick, ax=ax, u=u, bt=box_top: [_p3(ax, ap[ax], u, z), _p3(ax, brick, u, z), _p3(ax, brick, u, bt)]
            out[n] = dict(kind="drop", room=room, ax=ax, sg=sg, u=u, approach=tuple(ap), tail=tail, brick=brick, through=thr)
        else:                                                  # from the room behind: chase, S through the brick, chase
            far = brick - sg * wall_t                          # the brick face on the room side
            back = [c[0], c[1]]
            back[ax] = far - sg * (0.03 + EC["off"] + 0.05)
            room = _cd_room_at(rooms, back, 0.0)
            assert room, f"[through] {n}: no void behind it"
            ap = [c[0], c[1]]
            ap[ax] = far - sg * (0.015 + EC["off"])
            lvl = rooms[room]["level"]
            zs = lvl - 0.08
            tail = lambda z, ap=ap, far=far, brick=brick, ax=ax, u=u, bt=box_top, zs=zs: [
                _p3(ax, ap[ax], u, z), _p3(ax, far, u, z), _p3(ax, far, u, zs), _p3(ax, brick, u, zs - EC["s_v"]), _p3(ax, brick, u, bt)]
            out[n] = dict(kind="through", room=room, ax=ax, sg=-sg, u=u, approach=tuple(ap), tail=tail, brick=brick, far=far)
    return out


_CD_FORCE_THROUGH = ()


def _p3(ax, d, u, z):
    return (d, u, z) if ax == 0 else (u, d, z)


_CD_BRICK = []


def _cd_brick_boxes():
    if not _CD_BRICK:
        _CD_BRICK.extend(b for (el, _), x in qto(C_WALL).items() if el in ("brick", "concrete") for b in x["boxes"])
        _CD_BRICK.extend(b for (el, _), x in qto(C_COL).items() if el == "concrete" for b in x["boxes"])
    return _CD_BRICK


# ---------------------------------------------------------------- routing

def _cd_route_rooms(links, a, b):
    """Room sequence a → b (fewest walls, then open links)."""
    import heapq
    adj = {}
    for x in links:
        adj.setdefault(x[0], []).append((x[1], x))
        adj.setdefault(x[1], []).append((x[0], x))
    best, prev, pq = {a: 0}, {}, [(0, a)]
    while pq:
        d, r = heapq.heappop(pq)
        if r == b:
            break
        if d > best.get(r, 1e9):
            continue
        for s, lk in adj.get(r, []):
            nd = d + (1 if lk[2] == "wall" else 0.2)
            if nd < best.get(s, 1e9):
                best[s], prev[s] = nd, (r, lk)
                heapq.heappush(pq, (nd, s))
    if b not in best:
        return None
    seq, r = [], b
    while r != a:
        p, lk = prev[r]
        seq.append((p, r, lk))
        r = p
    return seq[::-1]


def _cd_layout():
    """Per circuit: tree of sharp 3D runs (rigid), flex runs, boxes, holes; the main."""
    rooms = _cd_rooms()
    _CD_ROOMS[:] = list(rooms.values())
    links = _cd_links(rooms)
    hard = _cd_hard()
    dev = _cd_devices()
    lights = {n: d for n, d in dev.items() if d["kind"] == "light"}
    pb = bpy.data.objects["EL_PB"]
    pbb = _el_bounds(pb)
    pb_face = pbb[0] if pb.data["sg"] > 0 else pbb[3]
    pb_brick = pb_face - 0.015 - 0.0006 * 3
    used_holes = []                                            # (wall key, u, z)
    chases_u = {}                                              # brick-face key → [u] of device chases
    for n, d in dev.items():
        if d["kind"] != "light":
            chases_u.setdefault((d["ax"], round(d["brick"], 3)), []).append(d["u"])
    res = dict(runs=[], flex=[], boxes=[], holes=[], segs={}, cond={}, errs=[])
    for ci, (cname, brk, wire, rcbo, members) in enumerate(CIRCUITS):
        names = []
        for m in members:
            if m.startswith("DL:"):
                names += sorted(n for n, d in lights.items() if d["room"] == m[3:])
            elif m == "EAVE":
                names += sorted(n for n, d in lights.items() if n.startswith("EL_EAVE"))
            else:
                names.append(m)
        assert all(n in dev for n in names), f"[circuit] {cname}: unknown device {[n for n in names if n not in dev]}"
        z_main = _cd_lane(cname, "main")
        u0 = (pbb[1] + pbb[4]) / 2 - 0.20 + EC["slot"] * ci
        pb_top = pbb[5]
        west = cname in WEST
        root = (pb_face - (0.015 + BRICK["t"] + 0.015 + EC["off"]) if west else pb_face + EC["off"], u0)
        res["runs"].append(dict(c=cname, pts=[(pb_brick, u0, pb_top), (pb_brick, u0, z_main), (root[0], root[1], z_main)], kind="home"))
        if west:
            res["holes"].append(dict(c=cname, key=(0, round(pb_brick, 3)), u=u0, z=z_main, a="living", b="bed1"))
        tree = [dict(room="bed1" if west else "living", a=root, b=root, z=z_main)]      # plan segments of this circuit
        order = sorted(names, key=lambda n: abs((dev[n].get("approach") or dev[n]["at"])[0] - root[0]) +
                       abs((dev[n].get("approach") or dev[n]["at"])[1] - root[1]))
        for n in order:
            d = dev[n]
            target = d["approach"] if d["kind"] != "light" else d["at"]
            troom = d["room"]
            # nearest room holding tree, by room route length
            best = None
            for seg in tree:
                seq = [] if seg["room"] == troom else _cd_route_rooms(links, seg["room"], troom)
                if seq is None:
                    continue
                if seq and any(lk[2] == "wall" and rooms[p]["zone"] == "lt" and rooms[q]["zone"] != "lt" for p, q, lk in seq):
                    continue
                cost = len(seq) * 10 + abs(target[0] - seg["a"][0]) + abs(target[1] - seg["a"][1])
                if best is None or cost < best[0]:
                    best = (cost, seg, seq)
            if best is None:
                res["errs"].append(f"[route] {cname}: no route to {n}")
                continue
            _, seg, seq = best
            walls_ = [x for x in seq if x[2][2] == "wall"]
            if d["kind"] == "drop" and d.get("through") and walls_ and walls_[-1][2][3] == d["ax"] and \
                    abs(walls_[-1][2][4] - (d["brick"] - d["sg"] * BRICK["t"] / 2)) < 0.07:
                d = dict(d["through"])                         # its own wall: from the room behind, S through the brick
                target, troom = d["approach"], d["room"]
                seq = seq[:seq.index(walls_[-1])]
                while seq and seq[-1][1] != troom:
                    seq = seq[:-1]
            # start on that segment: the point nearest the first goal
            goal = target
            first = next(((p, q, lk) for p, q, lk in seq if lk[2] == "wall"), None)
            if first:
                goal = _cd_portal_app(first[2], rooms, first[0], seg_point=None, toward=target)[0]
            start, branch = _cd_project(seg, goal)
            cur, cz, croom = start, seg["z"], seg["room"]
            pts = [(start[0], start[1], cz)]
            if branch or not (seg["a"] == seg["b"]):          # every start off the tree is a 4x4 box (not the root)
                res["boxes"].append(dict(c=cname, at=(start[0], start[1], cz), kind="branch"))
            ok = True
            for p, q, lk in seq:
                if lk[2] == "open":
                    croom = q
                    continue
                zq = _cd_lane(cname, rooms[q]["zone"])
                a_pt, b_pt, u, z_h = _cd_portal_pick(lk, rooms, p, q, cur, target, cz, zq, hard, used_holes, chases_u)
                if a_pt is None:
                    res["errs"].append(f"[hole] {cname}: no clear hole {p} → {q} for {n}")
                    ok = False
                    break
                # in room p: L from cur to the approach a_pt
                leg = _cd_Lc(cur, a_pt, cz, lk[3], hard)
                _cd_reg(tree, p, cur, leg, cz)
                pts += leg
                ax = lk[3]
                sgn_ = 1 if b_pt[ax] > a_pt[ax] else -1
                if rooms[q]["zone"] == "lt" and rooms[p]["zone"] != "lt":
                    near = lk[4] + (-0.035 if a_pt[ax] < lk[4] else 0.035)          # house-side brick face
                    pts = pts[:-1] + [_p3(ax, near, u, cz), _p3(ax, near, u, z_h)]
                elif abs(cz - z_h) > 1e-6:                             # slant down to the hole
                    pts = pts[:-1] + [(a_pt[0], a_pt[1], cz), _p3(ax, a_pt[ax] + sgn_ * 0.12, u, z_h)]
                if abs(zq - z_h) > 1e-6:                               # and up again on the far side
                    pts += [_p3(ax, b_pt[ax] - sgn_ * 0.12, u, z_h), (b_pt[0], b_pt[1], zq)]
                else:
                    pts += [(b_pt[0], b_pt[1], zq)]
                res["holes"].append(dict(c=cname, key=(lk[3], round(lk[4], 3)), u=u, z=z_h, a=p, b=q))
                cur, cz, croom = b_pt, zq, q
            if not ok:
                continue
            z_end = _cd_lane(cname, rooms[troom]["zone"])
            if d["kind"] == "light":
                leg = _cd_Lc(cur, target, cz, None, hard)
                _cd_reg(tree, troom, cur, leg, cz)
                pts += leg
                jb = (target[0], target[1], cz)
                res["boxes"].append(dict(c=cname, at=jb, kind="light"))
                res["flex"].append(dict(c=cname, pts=[(jb[0], jb[1], cz - EC["jb"][2] / 2), (jb[0], jb[1], d["top"] + 0.001)], dev=n))
            else:
                leg = _cd_Lc(cur, target, cz, d["ax"], hard)
                _cd_reg(tree, troom, cur, leg, cz)
                pts += leg
                pts += d["tail"](cz)[1:]
            pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 1e-6]
            res["runs"].append(dict(c=cname, pts=pts, kind="branch", dev=n))
    return res


def _cd_reg(tree, room, cur, leg, z):
    """Register the axis-aligned plan legs cur → leg points as tree segments of `room`."""
    a = cur
    for p in leg:
        tree.append(dict(room=room, a=(a[0], a[1]), b=(p[0], p[1]), z=z))
        a = p


def _cd_project(seg, goal):
    """Point of a plan segment nearest the goal (axis-aligned segment), and whether it is a branch (inside the segment)."""
    a, b = seg["a"], seg["b"]
    if abs(a[0] - b[0]) < 1e-9 and abs(a[1] - b[1]) < 1e-9:
        return a, False
    ax = 0 if abs(a[1] - b[1]) < 1e-9 else 1
    lo, hi = sorted((a[ax], b[ax]))
    t = min(max(goal[ax], lo), hi)
    p = [0.0, 0.0]
    p[ax], p[1 - ax] = t, a[1 - ax]
    return tuple(p), lo + 1e-6 < t < hi - 1e-6


def _cd_L(cur, tgt, z, last_ax):
    """Manhattan plan legs cur → tgt at height z (excluding cur), the last leg along `last_ax` (square to a wall); a
    lateral offset under 0.25 m becomes a gentle S (two small bends) instead of two square turns."""
    if abs(cur[0] - tgt[0]) < 1e-6 or abs(cur[1] - tgt[1]) < 1e-6:
        return [(tgt[0], tgt[1], z)]
    d = (tgt[0] - cur[0], tgt[1] - cur[1])
    m = 0 if abs(d[0]) >= abs(d[1]) else 1                    # main axis
    if abs(d[1 - m]) < 0.25 and (last_ax is None or last_ax == m):
        D = abs(d[m])
        if D < 0.45:
            return [(tgt[0], tgt[1], z)]                       # a short slant
        h = min(0.25, D / 2 - 0.10)
        sgn = 1 if d[m] > 0 else -1
        a = [0.0, 0.0]
        b = [0.0, 0.0]
        a[m], a[1 - m] = cur[m] + sgn * (D / 2 - h), cur[1 - m]
        b[m], b[1 - m] = cur[m] + sgn * (D / 2 + h), tgt[1 - m]
        return [(a[0], a[1], z), (b[0], b[1], z), (tgt[0], tgt[1], z)]
    if last_ax == 0:              # end moving along x: first along y
        mid = (cur[0], tgt[1])
    elif last_ax == 1:
        mid = (tgt[0], cur[1])
    else:
        mid = (tgt[0], cur[1]) if abs(tgt[0] - cur[0]) >= abs(tgt[1] - cur[1]) else (cur[0], tgt[1])
    return [(mid[0], mid[1], z), (tgt[0], tgt[1], z)]


def _cd_Lc(cur, tgt, z, last_ax, hard):
    """_cd_L, or the other orientation, or a dog-leg, whichever keeps the conduit clear of ties / columns / openings."""
    rad = EC["od"] / 2 + 0.005
    cands = [_cd_L(cur, tgt, z, last_ax)]
    if last_ax is None:
        cands.append(_cd_L(cur, tgt, z, 0))
        cands.append(_cd_L(cur, tgt, z, 1))
    for f in (0.25, 0.5, 0.75):
        if abs(cur[0] - tgt[0]) > 0.3 and last_ax != 1:
            xm = cur[0] + (tgt[0] - cur[0]) * f
            cands.append([(xm, cur[1], z), (xm, tgt[1], z), (tgt[0], tgt[1], z)])
        if abs(cur[1] - tgt[1]) > 0.3 and last_ax != 0:
            ym = cur[1] + (tgt[1] - cur[1]) * f
            cands.append([(cur[0], ym, z), (tgt[0], ym, z), (tgt[0], tgt[1], z)])
    rects = [d["rect"] for d in _CD_ROOMS] if _CD_ROOMS else []

    def in_void(pts):
        for i in range(len(pts) - 1):
            a, b = pts[i], pts[i + 1]
            n = max(2, int(math.dist(a, b) / 0.05) + 1)
            for k in range(n):
                t = k / (n - 1)
                q = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                if rects and not any(_cd_in(r, q, -0.12) for r in rects):
                    return False
        return True
    for c in cands:
        pts = [(cur[0], cur[1], z)] + c
        if in_void(pts) and all(_cd_line_clear(hard, pts[i], pts[i + 1], rad) for i in range(len(pts) - 1)):
            return [q for i, q in enumerate(c) if math.dist(q, pts[i]) > 1e-6]
    return cands[0]


_CD_ROOMS = []


def _cd_portal_app(lk, rooms, p, seg_point, toward):
    ax, pl, lo, hi = lk[3], lk[4], lk[5], lk[6]
    u = min(max(toward[1 - ax], lo), hi)
    side = -1 if rooms[p]["rect"][ax] < pl else 1
    a = [0.0, 0.0]
    a[ax], a[1 - ax] = pl + side * (0.05 + EC["off"]), u
    return tuple(a), u


def _cd_portal_pick(lk, rooms, p, q, cur, target, cz, zq, hard, used, chases_u):
    """A clear hole on the wall p | q near the line toward the target: (approach in p, approach in q, u, hole z)."""
    ax, pl, lo, hi = lk[3], lk[4], lk[5], lk[6]
    want = min(max(target[1 - ax], lo), hi)
    sp = -1 if (rooms[p]["rect"][ax] + rooms[p]["rect"][ax + 2]) / 2 < pl else 1   # p's side of the wall
    lt = rooms[q]["zone"] == "lt" or rooms[p]["zone"] == "lt"
    z_h = EC["lt_z"] if lt else cz
    key = (ax, round(pl, 3))
    for k in range(int((hi - lo) / 0.01) + 1):
        u = want + (k + 1) // 2 * 0.01 * (1 if k % 2 else -1)
        if not lo <= u <= hi:
            continue
        if any(h[0] == key and abs(h[1] - u) < 0.03 and abs(h[2] - z_h) < 0.03 for h in used):
            continue
        if any(abs(u - v) < 0.06 for (a_, br), us in chases_u.items() if a_ == ax and abs(br - pl) < 0.08 for v in us):
            continue
        a_pt = [0.0, 0.0]
        b_pt = [0.0, 0.0]
        a_pt[ax], a_pt[1 - ax] = pl + sp * (0.05 + EC["off"]), u
        b_pt[ax], b_pt[1 - ax] = pl - sp * (0.05 + EC["off"]), u
        rad = EC["od"] / 2 + 0.002
        if not _cd_line_clear(hard, _p3(ax, pl + sp * 0.07, u, z_h), _p3(ax, pl - sp * 0.07, u, z_h), rad):
            continue
        if lt and rooms[p]["zone"] != "lt" and not _cd_line_clear(hard, _p3(ax, pl + sp * 0.05, u, cz), _p3(ax, pl + sp * 0.05, u, z_h), rad):
            continue
        used.append((key, u, z_h))
        return tuple(a_pt), tuple(b_pt), u, z_h
    return None, None, None, None


# ---------------------------------------------------------------- build, wire, report

def _cd_clean(pts, keep=()):
    """Drop spikes (a point the run passes and comes straight back from) and jogs under 2 cm, so every corner has room
    for its bend; the ends and the points in `keep` (branch boxes) stay."""
    P = [tuple(p) for p in pts]
    changed = True
    while changed and len(P) > 2:
        changed = False
        for i in range(1, len(P) - 1):
            if any(math.dist(P[i], k) < 1e-6 for k in keep):
                continue
            a, b, c = Vector(P[i - 1]), Vector(P[i]), Vector(P[i + 1])
            u, w = b - a, c - b
            if u.length < 0.02 or w.length < 0.02 and i + 1 < len(P) - 1:
                del P[i]
                changed = True
                break
            if u.length > 1e-9 and w.length > 1e-9 and u.normalized().dot(w.normalized()) < -0.999:
                del P[i]
                changed = True
                break
    return P


def _cd_split(pts, bps):
    """Split a sharp polyline at every branch point lying on it (inserted as a vertex): no fillet across a box."""
    out = [list(pts[:1])]
    for i in range(len(pts) - 1):
        a, b = Vector(pts[i]), Vector(pts[i + 1])
        cuts = []
        for q in bps:
            Q = Vector(q)
            ab = b - a
            if ab.length < 1e-9:
                continue
            t = (Q - a).dot(ab) / ab.length_squared
            if 1e-6 < t <= 1 + 1e-9 and (a + ab * t - Q).length < 1e-6:
                cuts.append(t)
        for t in sorted(set(round(t, 9) for t in cuts)):
            P = tuple(a + (b - a) * min(t, 1.0))
            if math.dist(P, out[-1][-1]) > 1e-6:
                out[-1].append(P)
            out.append([P])
        if math.dist(tuple(b), out[-1][-1]) > 1e-6:
            out[-1].append(tuple(b))
    return [o for o in out if len(o) >= 2]


def _cd_wire(res):
    """{(size, colour role): metres} — conductors per piece as in the module doc, + slack per end."""
    out = {}
    meta = {c[0]: c for c in CIRCUITS}
    for r in res["runs"]:
        c = meta[r["c"]]
        L = sum(math.dist(r["pts"][i], r["pts"][i + 1]) for i in range(len(r["pts"]) - 1))
        n = 3
        if r["c"].startswith("L"):
            n = 2 if r.get("dev", "").startswith("EL_SW") else 4
        out[c[2]] = out.get(c[2], 0.0) + n * (L + 2 * EC["slack"])
    for f in res["flex"]:
        L = math.dist(f["pts"][0], f["pts"][1])
        out[2.5] = out.get(2.5, 0.0) + 3 * (L + 2 * EC["slack"])
    return out


def build_conduit():
    c = _clear(C_COND)
    _CD_BRICK.clear()
    pvc = mat("M_PVC_Conduit", (0.93, 0.93, 0.92), 0.5)
    flexm = mat("M_Flex", (0.85, 0.85, 0.85), 0.6)
    boxm = mat("M_JB", (0.30, 0.45, 0.80), 0.5)
    res = _cd_layout()
    assert not res["errs"], "; ".join(res["errs"][:6])
    by = {}
    for r in res["runs"]:
        bps = [b["at"] for b in res["boxes"] if b["c"] == r["c"] and b["kind"] == "branch"]
        for piece in _cd_split(r["pts"], bps):
            by.setdefault(r["c"], []).append(_fillet(_cd_clean(piece, bps), EC["r"]))
    for cname, paths in by.items():
        meta = next(x for x in CIRCUITS if x[0] == cname)
        c.objects.link(bpy.data.objects.new(f"CD_{cname}", _rebar_data(f"CD_{cname}", paths, EC["od"], pvc, element="conduit",
                                                                       type="PVC20", th="ท่อ PVC 1/2\" (20 มม.) ร้อยสาย", bar="PVC 20 mm", dia_mm=20,
                                                                       circuit=cname, breaker=meta[1], wire=meta[2], rcbo=meta[3])))
    fx = {}
    for f in res["flex"]:
        fx.setdefault(f["c"], []).append(f["pts"])
    for cname, paths in fx.items():
        c.objects.link(bpy.data.objects.new(f"CD_{cname}_Flex", _rebar_data(f"CD_{cname}_Flex", paths, 0.016, flexm, element="conduit",
                                                                            type="FLEX", th="ท่ออ่อนลูกฟูก 1/2\" (เข้าดวงโคม)", bar="Flex 16 mm",
                                                                            dia_mm=16, circuit=cname)))
    jw, jd, jh = EC["jb"]
    boxes = [(b["at"][0] - jw / 2, b["at"][1] - jd / 2, b["at"][2] - jh / 2, b["at"][0] + jw / 2, b["at"][1] + jd / 2, b["at"][2] + jh / 2)
             for b in res["boxes"]]
    if boxes:
        c.objects.link(bpy.data.objects.new("CD_Boxes", _boxes_data("CD_Boxes", boxes, boxm, element="jbox", type="JB44",
                                                                     th="กล่องพักสาย 4×4 (บนฝ้า)")))
    me = bpy.data.objects.new("CD_Qty", None)
    me["holes"] = len(res["holes"])
    for k, v in _cd_wire(res).items():
        me[f"thw_{k}"] = v
    c.objects.link(me)
    bpy.context.view_layer.update()
    build_main()
    return len(res["runs"])


def conduit_report():
    r = qto(C_COND)
    out = []
    for (el, tp), x in sorted(r.items()):
        if el == "conduit":
            m = sum(x["bars"])
            out.append(f"{x['th']}: {m:.1f} ม." + (f" → {math.ceil(m / EC['stock'] - 1e-9)} เส้น (ยาว {EC['stock']:.0f} ม.)" if tp != "FLEX" else ""))
        if el == "jbox":
            out.append(f"{x['th']}: {x['n'] and len(x['boxes'])} กล่อง")
    q = bpy.data.objects["CD_Qty"]
    for k in (1.5, 2.5, 4.0, 10, 16):
        if f"thw_{k}" in q:
            v = q[f"thw_{k}"]
            out.append(f"สาย THW {k:g} sq.mm: {v:.0f} ม." + (f" → {math.ceil(v / 100 - 1e-9)} ขด (100 ม.)" if k < 10 else " (ซื้อเป็นเมตร)"))
    boxes24 = sum(1 for o in _coll(C_ELEC).objects if o.data and o.data.get("type") in ("switch", "socket", "socket_wp", "wh"))
    out.append(f"บล็อกฝัง 2×4 + หน้ากาก Schneider AvatarOn สีเทา: {boxes24} ชุด · {EC['rod']} 1 ชุด · ตู้มิเตอร์ 1")
    out.append(f"รูเจาะผ่านผนังอิฐ: {q['holes']} รู")
    out.append("ตู้ Schneider Square D Classic 18 ช่อง: " + " · ".join(f"{c[0]} {c[1]}{' RCBO' if c[3] else ''}" for c in CIRCUITS))
    return "\n".join(out)


# ---------------------------------------------------------------- the main: meter → consumer unit

def _cd_main():
    """Meter box on the storage room's front outside wall; THW 2×16 + 10 earth in 1" PVC: up the outside face, through
    the soffit into the eave void, square through the wall over the storage ceiling, across to the living room at the
    main lane, down the consumer unit's chase. Points (sharp) + the meter box."""
    mx, my, mh = EC["meter"]
    walls = _obstacles()
    hit = _el_ray(walls, mx, my, GL + mh)                       # the storage front wall's outside plaster face
    _, ax, pl, sg = hit
    face = pl + sg * 0.0015                                     # on the paint
    mw, mhh, md = 0.30, 0.40, 0.15
    meter = (mx - mw / 2, face, GL + mh - mhh / 2, mx + mw / 2, face + md, GL + mh + mhh / 2) if sg > 0 else \
        (mx - mw / 2, face - md, GL + mh - mhh / 2, mx + mw / 2, face, GL + mh + mhh / 2)
    d_out = face + sg * (EC["od_main"] / 2 + 0.003)
    z = EC["lane_main"]
    brick_in = pl - sg * (0.015 + BRICK["t"])                  # storage-side brick face
    ap_in = brick_in - sg * (0.015 + EC["off"])
    pbo = bpy.data.objects["EL_PB"]
    pbb = _el_bounds(pbo)
    pb_face = pbb[0] if pbo.data["sg"] > 0 else pbb[3]
    u_pb = (pbb[1] + pbb[4]) / 2 + 0.20
    pb_brick = pb_face - 0.015 - 0.0018 - 0.002
    x_living = pb_face + 0.40
    y_hole = 3.40                                               # storage | living wall over the storage door D3 (brick)
    pts = [(mx, d_out, GL + mh + mhh / 2), (mx, d_out, z), (mx, ap_in, z), (mx, y_hole, z), (x_living, y_hole, z),
           (x_living, u_pb, z), (pb_brick, u_pb, z), (pb_brick, u_pb, pbb[5])]
    return pts, meter


def build_main():
    c = _coll(C_COND)
    for n in ("CD_MAIN", "EL_METER", "EL_ROD"):
        o = bpy.data.objects.get(n)
        if o:
            bpy.data.objects.remove(o)
    pts, meter = _cd_main()
    pvc = mat("M_PVC_Conduit", (0.93, 0.93, 0.92), 0.5)
    grey = mat("M_ElecGrey", (0.55, 0.56, 0.58), 0.5)
    cu = mat("M_Copper", (0.72, 0.45, 0.20), 0.4, 1.0)
    c.objects.link(bpy.data.objects.new("CD_MAIN", _rebar_data("CD_MAIN", [_fillet(pts, EC["r_main"])], EC["od_main"], pvc,
                                                               element="conduit", type="PVC32", th="ท่อ PVC 1 นิ้ว (32 มม.) สายเมน THW 2x16 + G 10",
                                                               bar="PVC 32 mm", dia_mm=32, circuit="MAIN")))
    c.objects.link(bpy.data.objects.new("EL_METER", _boxes_data("EL_METER", [meter], grey, element="meter", type="MT",
                                                                 th="ตู้มิเตอร์ + เมนเบรกเกอร์ 50 A (กฟภ. 15(45) A 1 เฟส)")))
    x = (meter[0] + meter[3]) / 2
    y = meter[1] - 0.30 if meter[1] < 0 else meter[4] + 0.30
    c.objects.link(bpy.data.objects.new("EL_ROD", _rebar_data("EL_ROD", [[(x, y, GL + 0.05), (x, y, GL - 2.44)]], 0.016, cu,
                                                              element="rod", type="GR", th=EC["rod"], bar="rod", dia_mm=16)))
    L = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    q = bpy.data.objects["CD_Qty"]
    q["thw_16"] = 2 * (L + 2 * EC["slack"])
    q["thw_10"] = L + 2 * EC["slack"] + 0.30 + 2.0              # + down to the rod
    q["holes"] = q["holes"] + 2
    bpy.context.view_layer.update()


# ---------------------------------------------------------------- ST12b selfcheck

def _cd_samples(path, step=0.01):
    out = []
    for i in range(len(path) - 1):
        a, b = Vector(path[i]), Vector(path[i + 1])
        n = max(1, int((b - a).length / step))
        for k in range(n):
            out.append(a + (b - a) * (k / n))
    out.append(Vector(path[-1]))
    return out


def _check_conduit(rows_before):
    """Read back: every device reached from the consumer unit by its circuit; nothing in a tie column, a column or an
    opening; nothing showing in a room under its ceiling or outside (the main's outside run excepted); runs of
    different circuits >= 1 OD apart; bends >= r; flex <= 1.8 m into each light."""
    objs = {o.name: o for o in _coll(C_COND).objects}
    fails = []
    hard = _cd_hard()
    gh = _Grid(hard)
    solids = _obstacles() + [b for n, v in _ft_boxes().items() for b in v] + \
        [b for (el, _), x in qto(C_CEIL).items() if el in ("ceiling", "soffit", "cline") for b in x["boxes"]]
    gs = _Grid(solids)
    rooms = _cd_rooms()
    elec = {o.name: o for o in _coll(C_ELEC).objects if o.data and o.data.get("element") == "elec"}
    pb = _el_bounds(elec["EL_PB"])
    paths = {}
    for n, o in objs.items():
        if o.type == "CURVE" and o.data.get("element") == "conduit":
            paths[n] = [[tuple(p) for p in sp] for sp in _world_bars(o)]
    ends = {}
    for n, ps in paths.items():
        cn = objs[n].data["circuit"]
        for p in ps:
            ends.setdefault(cn, []).extend([p[0], p[-1]])
    dev = _cd_devices()
    for cname, *_r, members in CIRCUITS:
        want = []
        for m in members:
            if m.startswith("DL:"):
                want += [n for n, d in dev.items() if d["kind"] == "light" and d["room"] == m[3:]]
            elif m == "EAVE":
                want += [n for n in dev if n.startswith("EL_EAVE")]
            else:
                want.append(m)
        for n in want:
            b = _el_bounds(elec[n])
            c = [(b[k] + b[k + 3]) / 2 for k in range(3)]
            if dev[n]["kind"] == "light":
                ok = any(abs(e[0] - c[0]) < 2e-3 and abs(e[1] - c[1]) < 2e-3 and abs(e[2] - b[5]) < 3e-3 for e in ends.get(cname, []))
            else:
                ax = dev[n]["ax"]
                ok = any(abs(e[1 - ax] - c[1 - ax]) < 3e-3 and b[2] - 0.01 < e[2] < b[5] + 0.06 and
                         abs(e[ax] - dev[n]["brick"]) < 0.004 for e in ends.get(cname, []))
            if not ok:
                fails.append(f"[connect] {cname}: {n} not reached")
        if not any(abs(e[2] - pb[5]) < 1e-3 and pb[1] - 0.05 <= e[1] <= pb[4] + 0.05 for e in ends.get(cname, [])):
            fails.append(f"[connect] {cname}: no home run from the consumer unit")
    jbs = []
    if "CD_Boxes" in objs:
        bm = _world_bm(objs["CD_Boxes"])
        try:
            jbs = _obj_boxes(bm, "CD_Boxes")
        finally:
            bm.free()

    def on_seg(s, a, b):
        a, b, s = Vector(a), Vector(b), Vector(s)
        ab = b - a
        t = 0.0 if ab.length < 1e-9 else max(0.0, min(1.0, (s - a).dot(ab) / ab.length_squared))
        return (a + ab * t - s).length
    for n, ps in paths.items():
        cn = objs[n].data["circuit"]
        if cn == "MAIN":
            continue
        segs = [(m, i, qq[k], qq[k + 1]) for m, qs in paths.items() if objs[m].data.get("circuit") == cn and objs[m].data["type"] != "FLEX"
                for i, qq in enumerate(qs) for k in range(len(qq) - 1)]
        for i, p in enumerate(ps):
            s = p[0]
            if abs(s[2] - pb[5]) < 1e-3:
                continue
            in_jb = any(all(b[k] - 1e-4 <= s[k] <= b[k + 3] + 1e-4 for k in range(3)) for b in jbs)
            if not in_jb and not any((m, j) != (n, i) and on_seg(s, a, b) < 0.003 for m, j, a, b in segs):
                fails.append(f"[connect] {n}: a run starts in the air at {tuple(round(v, 2) for v in s)}")
                break
    lights = [_el_bounds(o) for n, o in elec.items() if o.data["type"] in ("downlight", "eave")]
    wallb = [b for (el, _), x in qto(C_WALL).items() if el in ("brick", "concrete") for b in x["boxes"]]
    gw = _Grid(wallb)

    def near_wall(v):
        q = (v.x - 0.07, v.y - 0.07, v.z - 0.001, v.x + 0.07, v.y + 0.07, v.z + 0.001)
        return any(b[0] < q[3] and b[3] > q[0] and b[1] < q[4] and b[4] > q[1] and b[2] <= v.z <= b[5] for b in gw.near(q))
    samples = []
    for n, ps in paths.items():
        flex = objs[n].data["type"] == "FLEX"
        main = objs[n].data["circuit"] == "MAIN"
        r_min = EC["r_main"] if main else EC["r"]
        od = EC["od_main"] if main else 0.016 if flex else EC["od"]
        for pi, p in enumerate(ps):
            if flex and math.dist(p[0], p[-1]) > 1.8:
                fails.append(f"[flex] {n}: {math.dist(p[0], p[-1]):.2f} m")
            for v in _cd_samples(p):
                samples.append((n, pi, v, od))
                q = (v.x, v.y, v.z, v.x, v.y, v.z)
                if any(all(b[k] + od / 2 - 1e-3 < v[k] < b[k + 3] - od / 2 + 1e-3 for k in range(3)) for b in gh.near(q, od)):
                    fails.append(f"[tie] {n}: through a tie column / column / opening at {tuple(round(c, 3) for c in v)}")
                    break
                if any(all(b[k] - 1e-4 <= v[k] <= b[k + 3] + 1e-4 for k in range(3)) for b in gs.near(q, 1e-4)):
                    continue
                if flex and any(abs(v.x - (L[0] + L[3]) / 2) < 0.08 and abs(v.y - (L[1] + L[4]) / 2) < 0.08 for L in lights):
                    continue
                if main and v.z < 4.0 and _cd_room_at(rooms, v, 0.0) is None:
                    continue
                if near_wall(v):
                    continue                                    # passing the ceiling's edge in its notch (practice)
                room = _cd_room_at(rooms, v, -0.15)                # (traced rects stop at column plaster)
                if room is None or v.z < rooms[room]["level"] + 0.031 + od / 2 - 1e-3:
                    fails.append(f"[visible] {n}: conduit in sight at {tuple(round(c, 3) for c in v)}")
                    break
            P = [Vector(x) for x in p]
            for i in range(1, len(P) - 1):
                a, b = P[i] - P[i - 1], P[i + 1] - P[i]
                if a.length < 0.003 or b.length < 0.003:
                    continue
                th = a.angle(b)
                if th > math.radians(1.0):
                    R = min(a.length, b.length) / th
                    if R < r_min * 0.9:
                        fails.append(f"[bend] {n}: radius {R:.3f} < {r_min} at {tuple(round(c, 3) for c in P[i])}")
                        break
    cell = 0.05
    grid = {}
    for i, (n, pi, v, od) in enumerate(samples):
        grid.setdefault((int(v.x // cell), int(v.y // cell), int(v.z // cell)), []).append(i)
    cl = 0
    for (n, pi, v, od) in samples[::3]:
        k = (int(v.x // cell), int(v.y // cell), int(v.z // cell))
        cn = objs[n].data["circuit"]
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in grid.get((k[0] + dx, k[1] + dy, k[2] + dz), ()):
                        m, pj, w, odj = samples[j]
                        if objs[m].data["circuit"] != cn and (v - w).length < (od + odj) / 2 - 1e-3:
                            cl += 1
                            if cl == 1:
                                fails.append(f"[clash] {n} and {m} touch at {tuple(round(c, 3) for c in v)}")
    if fails:
        raise AssertionError(f"{len(fails)} failing in conduit:\n" + "\n".join(fails[:12]))
    tot = sum(math.dist(p[i], p[i + 1]) for ps in paths.values() for p in ps for i in range(len(p) - 1))
    return f"ST12b ok: {len(CIRCUITS)} circuits + main, conduit {tot:.1f} m, {len(paths)} conduit objects"
