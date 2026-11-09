# ST07 mutation suite: build the roof frame with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st07.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
G = globals()
SPEC = copy.deepcopy((ROOF, LEAN, SECTIONS))
SCAL = {k: G[k] for k in ("PITCH", "PLATE_TOP", "EAVE")}
LAT = _lat
problems = 0


def restore():
    for live, spec in zip((ROOF, LEAN, SECTIONS), SPEC):
        live.clear()
        live.update(copy.deepcopy(spec))
    G.update(SCAL)
    G["_lat"] = LAT


def with_(d, **kw):
    def f():
        d.update(kw)
        build_roof_frame()
    return f


def scal(**kw):
    def f():
        G.update(kw)
        build_roof_frame()
    return f


def no_cut():
    G["_lat"] = lambda: 0.0
    build_roof_frame()


def move(name, dx=0.0, dz=0.0):
    def f():
        build_roof_frame()
        o = bpy.data.objects[name]
        o.location.x += dx
        o.location.z += dz
        bpy.context.view_layer.update()
        o.data["p0"] = list(o.matrix_world @ __import__("mathutils").Vector(o.data["p0"]) - o.matrix_world.translation + o.location) if False else o.data["p0"]
    return f


MUTATIONS = [
    ("pitch 25°", scal(PITCH=25.0), ["pitch", "seat", "planes", "battens", "posts"]),
    ("wall plate top +4.20", scal(PLATE_TOP=4.20), ["plate", "seat", "posts", "battens", "planes"]),
    ("eave 0.90", scal(EAVE=0.90), ["eave", "seat", "battens", "planes"]),
    ("rafters @1.20", with_(ROOF, rafter_s=1.20), ["spacing"]),
    ("battens first course 0.40", with_(ROOF, batten_first=0.40), ["battens"]),
    ("battens @0.40", with_(ROOF, batten_max=0.40), ["battens"]),
    ("rafters not cut back at hips / valleys", no_cut, ["clash"]),
    ("2C 125 built as 2C 150", with_(SECTIONS, **{"2C125": ("2C", (0.150, 0.050, 0.020, 0.0023))}), ["section", "plate", "clash", "planes", "posts"]),
    ("C100 rafters 2.0 mm", with_(SECTIONS, C100=("C", (0.100, 0.050, 0.020, 0.0020))), ["section"]),
    ("lean-to / canopy top +3.40", with_(LEAN, top=3.40), ["lean"]),
    ("lean-to purlins @1.50", with_(LEAN, s=1.50), ["lean"]),
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

# a king post dropped 5 cm (model edit): the post check reads the object, not the spec
build_roof_frame()
o = bpy.data.objects["RF_post_003"]
o.location.z -= 0.05
bpy.context.view_layer.update()
try:
    selfcheck()
    print("MISSED  king post dropped 5 cm (object moved, props kept)")
except AssertionError as e:
    print("caught  king post dropped 5 cm:", str(e).splitlines()[-1][:100])
o.location.z += 0.05
bpy.context.view_layer.update()

build_roof_frame()
print("control:", selfcheck()[-160:])
n0 = len(_coll(C_ROOF).objects)
build_roof_frame()
assert len(_coll(C_ROOF).objects) == n0, "re-run duplicated objects"
print(f"TESTS DONE problems: {problems}")
assert problems == 0
