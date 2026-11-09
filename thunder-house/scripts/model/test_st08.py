# ST08 mutation suite: build the roof cover with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st08.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
G = globals()
SPEC = copy.deepcopy((TILE, FASCIA, SHEET, LEAN_ROOFS))
BED, LOOPS = _bed_z, _plane_loops
problems = 0


def restore():
    for live, spec in zip((TILE, FASCIA, SHEET, LEAN_ROOFS), SPEC):
        live.clear()
        live.update(copy.deepcopy(spec))
    G["_bed_z"], G["_plane_loops"] = BED, LOOPS


def with_(d, **kw):
    def f():
        d.update(kw)
        build_roof_cover()
    return f


def bed_low():   # tiles laid straight on the rafters (battens forgotten)
    G["_bed_z"] = lambda dd: _z_top(dd)
    build_roof_cover()


def drop_plane():   # one roof plane left untiled
    full = LOOPS()
    G["_plane_loops"] = lambda: dict(list(full.items())[1:])
    build_roof_cover()


def shrink_bed():   # a bed polygon pulled in 10 cm from the eave
    full = LOOPS()
    p0 = next(iter(full))
    ax, k, dr = p0
    e = k - dr * EAVE
    def moved(loop):
        out = []
        for x, y in loop:
            c = (x, y)[ax]
            if abs(c - e) < 1e-6:
                c = e + dr * 0.10
            out.append((c, y) if ax == 0 else (x, c))
        return out
    G["_plane_loops"] = lambda: {p: ([moved(l) for l in ls] if p == p0 else ls) for p, ls in full.items()}
    build_roof_cover()


def move(name, dz=0.0, dx=0.0):
    def f():
        build_roof_cover()
        o = bpy.data.objects[name]
        o.location.z += dz
        o.location.x += dx
        bpy.context.view_layer.update()
    return f


MUTATIONS = [
    ("tiles on the rafters (no battens)", bed_low, ["tiles"]),
    ("a plane left untiled", drop_plane, ["tiles"]),
    ("tile bed 10 cm short of the eave", shrink_bed, ["tiles"]),
    ("fascia 20 cm board", with_(FASCIA, h=0.20), ["fascia"]),
    ("fascia 2.5 cm thick", with_(FASCIA, t=0.025), ["fascia"]),
    ("fascia slid 3 cm out", move("FS_Fascia", dx=0.03), ["fascia"]),
    ("sheet floating 5 cm", move("MS_lean-to", dz=0.05), ["sheet"]),
    ("canopy sheet short", with_(LEAN_ROOFS, canopy=dict(x=(5.115, 9.0), y=(-1.0, 0.885), supports=[(0.0, 5.115, 9.385), (0.835, 5.115, 9.385)])), ["sheet"]),
]

for name, build, tags in MUTATIONS:
    try:
        build()
    except AssertionError as e:
        print(f"caught  {name}: builder refused ({str(e)[:80]})")
        restore()
        continue
    restore()
    try:
        selfcheck()
        print(f"MISSED  {name}")
        problems += 1
    except AssertionError as e:
        msg = str(e)
        hit = [t for t in tags if f"[{t}]" in msg]
        print(f"{'caught ' if hit else 'WRONG  '} {name}: {msg.splitlines()[0][:110]} | {msg.splitlines()[-1][:90]}")
        problems += not hit

build_roof_cover()
print("control:", selfcheck()[-120:])
n0 = len(_coll(C_COVER).objects)
build_roof_cover()
assert len(_coll(C_COVER).objects) == n0, "re-run duplicated objects"
print(f"TESTS DONE problems: {problems}")
assert problems == 0
