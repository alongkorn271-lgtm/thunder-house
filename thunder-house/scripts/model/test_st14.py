# ST14 mutation suite: doors / windows with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st14.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
G = globals()
SPEC = {k: copy.deepcopy(G[k]) for k in ("UN", "UN_SWING")}
ORIG = {k: G[k] for k in ("_un_layout",)}
problems = 0


def restore():
    for k, v in SPEC.items():
        G[k].clear()
        G[k].update(copy.deepcopy(v))
    G.update(ORIG)                                        # (the glass material is reset by the next build)


def layout(edit):
    def f():
        lay = ORIG["_un_layout"]
        def l():
            d = lay()
            edit(d)
            return d
        G["_un_layout"] = l
        build_units()
    return f


def mirror_w1(d):
    for info, parts in d:
        if info["tp"] == "W1":
            kc, ax = info["kc"], info["ax"]
            k0, k1 = (1, 4) if ax == 0 else (0, 3)
            for key in ("sash", "glass"):
                parts[key] = [tuple((2 * kc - b[k1] if i == k0 else 2 * kc - b[k0] if i == k1 else b[i]) for i in range(6)) for b in parts[key]]
            break


def drop_unit(d):
    del d[-1]


def wide_leaf(d):
    for info, parts in d:
        if info["tp"] == "D3":
            ax = info["ax"]
            b = list(parts["leaf"][0])
            if info["hinge"] == "a":
                b[ax + 3] += 0.9
            else:
                b[ax] -= 0.9
            parts["leaf"][0] = tuple(b)
            break


def flip_swing():
    k = next(iter(UN_SWING))
    x, y = UN_SWING[k]
    w = next(w for w in WALLS if _wl(w)[0] == k[0])
    kc, ax = _wl(w)[2], _wl(w)[1]
    UN_SWING[k] = (x, 2 * kc - y) if ax == 0 else (2 * kc - x, y)
    build_units()


def opaque_glass():
    build_units()
    bpy.data.materials["M_Glass5"].diffuse_color = (0.85, 0.92, 0.95, 1.0)


MUTATIONS = [
    ("frames tight in the plaster (no 5 mm gap)", lambda: (UN.update(gap=0.0), build_units()), ["snug", "clash"]),
    ("frames 12 cm deep", lambda: (UN.update(depth=0.12), build_units()), ["snug", "clash"]),
    ("W1 fixed panes on the room side", layout(mirror_w1), ["slide"]),
    ("glass 4 mm", lambda: (UN.update(glass=0.004), build_units()), ["glass"]),
    ("glass opaque in solid view", opaque_glass, ["glass"]),
    ("door leaves on the floor", lambda: (UN.update(floor_gap=0.0), build_units()), ["leaf", "clash"]),
    ("a unit missing", layout(drop_unit), ["count"]),
    ("a door opening out of its room", flip_swing, ["swing"]),
    ("a D3 leaf 0.9 m too wide", layout(wide_leaf), ["swing", "clash"]),
]

for name, build, tags in MUTATIONS:
    try:
        build()
    except AssertionError as e:
        print(f"caught  {name}: builder refused ({str(e)[:80]})")
        restore()
        build_units()
        continue
    restore()
    try:
        selfcheck()
        print(f"MISSED  {name}")
        problems += 1
    except AssertionError as e:
        msg = str(e)
        hit = [t for t in tags if f"[{t}]" in msg]
        print(f"{'caught ' if hit else 'WRONG  '} {name}: {msg.splitlines()[0][:80]} | {msg.splitlines()[1][:120] if len(msg.splitlines()) > 1 else ''}")
        problems += not hit

build_units()
print("control:", selfcheck()[-150:])
n0 = len(_coll(C_UNIT).objects)
build_units()
assert len(_coll(C_UNIT).objects) == n0, "re-run duplicated objects"
print(f"TESTS DONE problems: {problems}")
assert problems == 0
