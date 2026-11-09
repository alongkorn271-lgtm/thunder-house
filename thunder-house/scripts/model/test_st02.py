# ST02 mutation suite: build the stubs with one thing wrong, put the spec back, selfcheck must fail with its own tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st02.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
SPEC = copy.deepcopy((STUBS, STUB_GRIDS, GB_LINES))
problems = 0


def restore():
    for live, spec in zip((STUBS, STUB_GRIDS), SPEC[:2]):
        live.clear()
        live.update(copy.deepcopy(spec))
    GB_LINES[:] = copy.deepcopy(SPEC[2])


def with_stub(**kw):
    def f():
        STUBS["P1"].update(kw)
        build_stubs()
    return f


def move(name, dx=0.0, dz=0.0):
    def f():
        build_stubs()
        o = bpy.data.objects[name]
        o.location.x += dx
        o.location.z += dz
        bpy.context.view_layer.update()
    return f


def drop_stub():
    STUB_GRIDS["P1"] = STUB_GRIDS["P1"][:-1]
    build_stubs()


def beams_up():   # every ground beam drawn 10 cm higher → stubs 10 cm taller
    GB_LINES[:] = [(a, b, top + 0.10, tp) for a, b, top, tp in GB_LINES]
    build_stubs()


MUTATIONS = [
    ("stub sunk 5 cm", move("P1_C2", dz=-0.05), ["level", "clash"]),
    ("stub moved 5 cm", move("P1_E3", dx=0.05), ["position"]),
    ("ties @0.20", with_stub(s=0.20), ["spacing", "tie length"]),
    ("ties first 0.10 from the ends", with_stub(first=0.10), ["spacing"]),
    ("cover 0.04", with_stub(cover=0.04), ["cover", "tie length"]),
    ("4 starters instead of 6", with_stub(nbar=4), ["bars", "rebar length"]),
    ("starters lifted 5 cm off the mat", move("P1_G6_Bars", dz=0.05), ["starter"]),
    ("starters shifted 2 cm (same length)", move("P1_A4_Bars", dx=0.02), ["cover", "starter"]),
    ("L-foot 0.10", with_stub(foot=0.10), ["rebar length", "starter"]),
    ("lap 0.40", with_stub(lap=0.40), ["rebar length", "starter"]),
    ("stub missing", drop_stub, ["count"]),
    ("beams 10 cm higher", beams_up, ["level", "stub concrete"]),
]

for name, build, tags in MUTATIONS:
    try:
        build()
    except AssertionError as e:   # the builder itself refused it: also caught
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
        print(f"{'caught ' if hit else 'WRONG  '} {name}: {msg.splitlines()[0][:110]}")
        problems += not hit

# clean control: the real spec passes, and a re-run makes no duplicates
build_stubs()
print("control:", selfcheck())
n = build_stubs()
assert len(_coll(C_STUB).objects) == n * 4, "re-run duplicated objects"
assert not [d.name for d in list(bpy.data.meshes) + list(bpy.data.curves) if d.name.startswith("P1_") and "." in d.name], ".001 data"
print("shared data:", sorted({o.data.name for o in _coll(C_STUB).objects if o.data}))
print("control re-run:", selfcheck())
print(f"TESTS DONE problems: {problems}")
assert problems == 0
