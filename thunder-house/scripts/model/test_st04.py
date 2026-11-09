# ST04 mutation suite: build the floor with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st04.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
SPEC = copy.deepcopy((PS, TOPPING, SSLAB, FLOOR_PANELS))
problems = 0


def restore():
    for live, spec in zip((PS, TOPPING, SSLAB), SPEC[:3]):
        live.clear()
        live.update(copy.deepcopy(spec))
    FLOOR_PANELS[:] = copy.deepcopy(SPEC[3])


def with_(d, **kw):
    def f():
        d.update(kw)
        build_floor()
    return f


def move(name, dx=0.0, dz=0.0):
    def f():
        build_floor()
        o = bpy.data.objects[name]
        o.location.x += dx
        o.location.z += dz
        bpy.context.view_layer.update()
    return f


def drop(name):
    def f():
        FLOOR_PANELS[:] = [p for p in FLOOR_PANELS if f"{p[0]}-{p[1]}" != name]
        build_floor()
    return f


def as_kind(name, kind):
    def f():
        FLOOR_PANELS[:] = [(a, b, kind if f"{a}-{b}" == name else k) for a, b, k in FLOOR_PANELS]
        build_floor()
    return f


MUTATIONS = [
    ("plank bearing 0.04", with_(PS, bear=0.04), ["planks", "bearing"]),
    ("planks 0.30 wide", with_(PS, w=0.30), ["planks", "topping"]),
    ("planks 6 cm thick", with_(PS, t=0.06), ["level", "planks"]),
    ("PS panel slid 5 cm", move("PS_C5-D6", dx=0.05), ["planks", "bearing", "clash"]),
    ("topping to +0.85", with_(TOPPING, top=0.85), ["level", "topping"]),
    ("no column holes", with_(TOPPING, holes=False), ["planks", "topping", "holes"]),
    ("mesh @0.15", with_(TOPPING, mesh_s=0.15), ["mesh"]),
    ("mesh cover 0.01", with_(TOPPING, mesh_cover=0.01), ["mesh"]),
    ("hook bars @0.40", with_(TOPPING, hook_s=0.40), ["hooks"]),
    ("hook bars 0.50 over inner beams", with_(TOPPING, hook_in=0.50), ["hooks"]),
    ("S slab 0.10 thick", with_(SSLAB, t=0.10), ["level", "slab concrete"]),
    ("S slab raised to +0.80", move("S_B4-C5", dz=0.10), ["level"]),
    ("S bars short @0.20", with_(SSLAB, s_short=0.20), ["slab bars", "rebar length"]),
    ("S cover 0.03", with_(SSLAB, cover=0.03), ["slab bars"]),
    ("S top bars L/5", with_(SSLAB, top_frac=0.20), ["rebar length"]),
    ("bath 2 left out", drop("D5a-F6"), ["count"]),
    ("bath 1 built as PS", as_kind("E1-Gb1a", "PS"), ["count"]),
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
        print(f"{'caught ' if hit else 'WRONG  '} {name}: {msg.splitlines()[0][:110]} | {msg.splitlines()[-1][:80]}")
        problems += not hit

build_floor()
print("control:", selfcheck())
n0 = len(_coll(C_FLOOR).objects)
build_floor()
assert len(_coll(C_FLOOR).objects) == n0, "re-run duplicated objects"
assert not [d.name for d in list(bpy.data.meshes) + list(bpy.data.curves)
            if d.name.startswith(("PS_", "S_", "TOP_")) and d.name[-4:-3] == "." and d.name[-3:].isdigit()], ".001 data"
print("control re-run:", selfcheck())
print(f"TESTS DONE problems: {problems}")
assert problems == 0
