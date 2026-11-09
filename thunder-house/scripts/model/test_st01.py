# ST01 mutation suite: build with one thing wrong, put the spec back, selfcheck must fail with its own tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st01.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
SPEC_T, SPEC_F = copy.deepcopy(TYPES), copy.deepcopy(FOOTINGS)
problems = 0


def with_types(**kw):
    def f():
        TYPES["F1"].update(kw)
        TYPES["F1"]["bot"] = TYPES["F1"]["exc"] + TYPES["F1"]["sand"] + TYPES["F1"]["lean"]
        build_footings()
    return f


def drop_footing():
    FOOTINGS["F1"] = FOOTINGS["F1"][:-1]
    build_footings()


def move(name, dx=0.0, dz=0.0):
    def f():
        build_footings()
        o = bpy.data.objects[name]
        o.location.x += dx
        o.location.z += dz
        bpy.context.view_layer.update()
    return f


def overlap():
    build_footings()   # a second footing concrete pushed into a neighbour's
    o = bpy.data.objects["F1_C3"]
    o.location.x -= 1.30
    bpy.context.view_layer.update()


MUTATIONS = [
    ("footing thicker 0.30", with_types(T=0.30), ["concrete"]),
    ("footing 1.00 wide", with_types(B=1.00), ["concrete"]),
    ("bars @0.15", with_types(s=0.15), ["rebar length", "spacing"]),
    ("bottom cover 0.05", with_types(bottom=0.05), ["cover"]),
    ("side cover 0.03", with_types(side=0.03), ["rebar length", "cover"]),
    ("mat shifted 3 cm (same length)", move("F1_E2_Rebar", dx=0.03), ["cover"]),
    ("sand 0.05 (footing 5 cm high)", with_types(sand=0.05, exc=-1.60), ["sand", "level"]),
    ("pit dug only to −1.50", with_types(exc=-1.50, sand=0.0001, lean=0.0001), ["level", "lean", "sand", "pit"]),
    ("pit 1.40 wide", with_types(work=0.10), ["pits"]),
    ("footing missing", drop_footing, ["count"]),
    ("footing moved 5 cm", move("F1_C2", dx=0.05), ["position"]),
    ("footing sunk 5 cm", move("F1_G6", dz=-0.05), ["level", "pit"]),
    ("footings overlap", overlap, ["clash", "position"]),
]

for name, build, tags in MUTATIONS:
    try:
        build()
    except AssertionError as e:   # the builder itself refused it: also caught
        print(f"caught  {name}: builder refused ({str(e)[:80]})")
        TYPES.clear(); TYPES.update(copy.deepcopy(SPEC_T)); FOOTINGS.clear(); FOOTINGS.update(copy.deepcopy(SPEC_F))
        continue
    TYPES.clear(); TYPES.update(copy.deepcopy(SPEC_T)); FOOTINGS.clear(); FOOTINGS.update(copy.deepcopy(SPEC_F))
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
build_footings()
print("control:", selfcheck())
n = build_footings()
assert len(_coll(C_FOOT).objects) == n * 6, "re-run duplicated objects"
assert not [d.name for d in list(bpy.data.meshes) + list(bpy.data.curves) if d.name.startswith("F1_") and "." in d.name], ".001 data"
print("control re-run:", selfcheck())
print(f"TESTS DONE problems: {problems}")
assert problems == 0
