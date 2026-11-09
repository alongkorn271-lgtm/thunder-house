# ST03 mutation suite: build the ground beams with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st03.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
SPEC = copy.deepcopy((GBEAM, BEAM_TYPES, GB_LINES))
problems = 0


def restore():
    for live, spec in zip((GBEAM, BEAM_TYPES), SPEC[:2]):
        live.clear()
        live.update(copy.deepcopy(spec))
    GB_LINES[:] = copy.deepcopy(SPEC[2])


def with_gb(**kw):
    def f():
        GBEAM.update(kw)
        build_ground_beams()
    return f


def with_type(tp, **kw):
    def f():
        BEAM_TYPES[tp].update(kw)
        build_ground_beams()
    return f


def move(name, dx=0.0, dz=0.0):
    def f():
        build_ground_beams()
        o = bpy.data.objects[name]
        o.location.x += dx
        o.location.z += dz
        bpy.context.view_layer.update()
    return f


def retype(a, b, tp):
    def f():
        GB_LINES[:] = [(p, q, top, tp if (p, q) == (a, b) else t) for p, q, top, t in GB_LINES]
        build_ground_beams()
    return f


def drop_span():   # the x 10.5 span A5a–B5a left out (its corner then rests on the A run end only)
    GB_LINES[:] = [s for s in GB_LINES if s[:2] != ("A5a", "B5a")]
    build_ground_beams()


MUTATIONS = [
    ("beam run slid 2 cm into a joint", move("GB_C1-C6", dx=0.02), ["position", "clash"]),
    ("beam run 5 cm lower", move("GB_G1-G6", dz=-0.05), ["level", "clash"]),
    ("joint raised 1 cm", move("J1_C1", dz=0.01), ["level", "clash"]),
    ("stirrups @0.20", with_gb(s=0.20), ["stirrups", "stirrup length"]),
    ("cover 0.035", with_gb(cover=0.035), ["cover", "rebar length", "stirrup length"]),
    ("lap 0.40", with_gb(lap=0.40), ["laps", "rebar length"]),
    ("hooks 0.10", with_gb(hook=0.10), ["laps", "rebar length"]),
    ("support bars L/5", with_gb(sup=0.20), ["rebar length"]),
    ("B2 with 1 special", with_type("B2", nsp=1), ["rebar length"]),
    ("B1 without its 3rd bottom bar", with_type("B1", extra=0), ["rebar length"]),
    ("span C2–C3 built as B3", retype("C2", "C3", "B3"), ["rebar length"]),
    ("lean 0.10", with_gb(lean=0.10), ["lean", "sand", "clash"]),
    ("lean strips 0.10 wider", with_gb(pad=0.10), ["lean", "sand"]),
    ("span left out", drop_span, ["count", "beam concrete"]),
    ("stub sunk 5 cm under its joint", lambda: (build_ground_beams(), _sink("P1_C3")), ["level", "clash"]),
]


def _sink(name):
    bpy.data.objects[name].location.z -= 0.05
    bpy.context.view_layer.update()


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
        print(f"{'caught ' if hit else 'WRONG  '} {name}: {msg.splitlines()[0][:110]}")
        problems += not hit
    bpy.data.objects["P1_C3"].location.z = TYPES["F1"]["bot"] + TYPES["F1"]["T"]   # undo _sink
    bpy.context.view_layer.update()

build_stubs()
build_ground_beams()
print("control:", selfcheck())
n0 = len(_coll(C_GB).objects)
build_ground_beams()
assert len(_coll(C_GB).objects) == n0, "re-run duplicated objects"
assert not [d.name for d in list(bpy.data.meshes) + list(bpy.data.curves)
            if d.name.startswith(("GB_", "J1_")) and "." in d.name.split("_", 1)[1].replace("1a", "").replace("5a", "")], ".001 data"
print("joint data:", sorted({o.data.name for o in _coll(C_GB).objects if o.name.startswith("J1_") and o.data}))
print("control re-run:", selfcheck())
print(f"TESTS DONE problems: {problems}")
assert problems == 0
