# ST09 mutation suite: build the ceilings with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st09.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
G = globals()
SPEC = copy.deepcopy((CEIL, SOFFIT, ROOMS, LEANTO_X))
problems = 0


def restore():
    for live, spec in zip((CEIL, SOFFIT), SPEC[:2]):
        live.clear()
        live.update(copy.deepcopy(spec))
    ROOMS[:] = copy.deepcopy(SPEC[2])
    G["LEANTO_X"] = SPEC[3]


def with_(d, **kw):
    def f():
        d.update(kw)
        build_ceilings()
    return f


def rooms(fn):
    def f():
        ROOMS[:] = fn(ROOMS)
        build_ceilings()
    return f


def move(name, dx=0.0, dz=0.0):
    def f():
        build_ceilings()
        o = bpy.data.objects[name]
        o.location.x += dx
        o.location.z += dz
        bpy.context.view_layer.update()
    return f


def lean_narrow():
    G["LEANTO_X"] = (3.5, 9.5)
    build_ceilings()


MUTATIONS = [
    ("kitchen ceiling at +3.20", rooms(lambda R: [(n, s, 3.20 if n == "kitchen" else l, t) for n, s, l, t in R]), ["level"]),
    ("bath 2 left unceiled", rooms(lambda R: [r for r in R if r[0] != "bath2"]), ["count"]),
    ("cross runners @0.60", with_(CEIL, s_cross=0.60), ["runners"]),
    ("mains @0.80", with_(CEIL, s_main=0.80), ["runners", "hangers"]),
    ("hangers @1.50", with_(CEIL, hang=1.50, hang_end=1.50), ["hangers"]),
    ("hangers short of the steel", move("CE_bed1_Hangers", dz=-0.05), ["hangers"]),
    ("living ceiling slid 5 cm", move("CE_living_Board", dx=0.05), ["boards", "clash", "runners"]),
    ("soffit 5 cm lower", with_(SOFFIT, above_fascia=-0.0246), ["soffit", "level"]),
    ("soffit under the lean-to too", lean_narrow, ["soffit"]),
    ("no fascia-side soffit runner", with_(SOFFIT, edge=0.15), ["soffit"]),
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

build_ceilings()
print("control:", selfcheck()[-90:])
n0 = len(_coll(C_CEIL).objects)
build_ceilings()
assert len(_coll(C_CEIL).objects) == n0, "re-run duplicated objects"
print(f"TESTS DONE problems: {problems}")
assert problems == 0
