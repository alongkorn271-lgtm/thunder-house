# ST06 mutation suite: build the walls with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st06.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
SPEC = copy.deepcopy((BRICK, TIE, PLASTER, OPENINGS, WALLS))
ZONES = _above_ceiling_zones
problems = 0


def restore():
    for live, spec in zip((BRICK, TIE, PLASTER, OPENINGS), SPEC[:4]):
        live.clear()
        live.update(copy.deepcopy(spec))
    WALLS[:] = copy.deepcopy(SPEC[4])
    globals()["_above_ceiling_zones"] = ZONES


def full_plaster():   # inside plaster left up to the wall top above the ceilings
    globals()["_above_ceiling_zones"] = lambda wall_boxes: []
    build_walls()


def with_(d, **kw):
    def f():
        d.update(kw)
        build_walls()
    return f


def wall_edit(i, **kw):
    def f():
        a, b, flush, lean, ops = WALLS[i]
        v = dict(a=a, b=b, flush=flush, lean=lean, ops=ops)
        v.update(kw)
        WALLS[i] = (v["a"], v["b"], v["flush"], v["lean"], v["ops"])
        build_walls()
    return f


def move(name, dx=0.0):
    def f():
        build_walls()
        o = bpy.data.objects[name]
        o.location.x += dx
        bpy.context.view_layer.update()
    return f


MUTATIONS = [
    ("a W4 left out", wall_edit(5, ops=[("W4", 7.00), ("W5", 3.16)]), ["openings"]),
    ("W1 built 2.00 wide", with_(OPENINGS, W1=(2.00, 1.20, 0.90)), ["openings"]),
    ("W5 sill 1.50", with_(OPENINGS, W5=(0.80, 0.50, 1.50)), ["openings"]),
    ("A line wall on the grid (not flush)", wall_edit(0, flush=0), ["flush"]),
    ("kitchen wall up to +4.30", wall_edit(0, lean=False), ["level"]),
    ("wall slid 5 cm", move("WL_E2-G2", dx=0.05), ["flush", "clash"]),
    ("brick panels up to 3.5 m", with_(TIE, panel=3.5), ["ties"]),
    ("tie columns 5 cm", with_(TIE, w=0.05), ["ties", "band"]),
    ("no mid-height band", with_(TIE, band_min_h=9.0), ["band"]),
    ("slivers left as brick", with_(TIE, sliver_u=0.0, sliver_z=0.0), ["ties"]),
    ("plaster 1.0 cm", with_(PLASTER, t=0.010), ["plaster", "openings"]),
    ("inside plaster to the wall top", full_plaster, ["plaster"]),
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
        print(f"{'caught ' if hit else 'WRONG  '} {name}: {msg.splitlines()[0][:100]} | {msg.splitlines()[-1][:100]}")
        problems += not hit

build_walls()
print("control:", selfcheck()[-110:])
n0 = len(_coll(C_WALL).objects)
build_walls()
assert len(_coll(C_WALL).objects) == n0, "re-run duplicated objects"
print(f"TESTS DONE problems: {problems}")
assert problems == 0
