# ST05 mutation suite: build the columns with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st05.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
SPEC = copy.deepcopy(COL)
G = globals()
problems = 0


def restore():
    COL.clear()
    COL.update(copy.deepcopy(SPEC))
    G["COL_TOP_LEAN"], G["LEAN_ROWS"] = 3.30 - 0.125, ("A", "B")


def with_(**kw):
    def f():
        COL.update(kw)
        build_columns()
    return f


def move(name, dx=0.0, dz=0.0):
    def f():
        build_columns()
        o = bpy.data.objects[name]
        o.location.x += dx
        o.location.z += dz
        bpy.context.view_layer.update()
    return f


def all_main():   # the lean-to columns built to +4.30 like the house
    G["LEAN_ROWS"] = ()
    build_columns()


MUTATIONS = [
    ("column moved 5 cm", move("C1_C3", dx=0.05), ["position", "clash"]),
    ("column sunk 5 cm into its joint", move("C1_G6", dz=-0.05), ["level", "clash"]),
    ("lean-to columns to +4.30", all_main, ["plate", "column concrete"]),
    ("ties @0.20", with_(s=0.20), ["ties", "tie length"]),
    ("ties only above the beam", with_(tie_from=GB_TOP), ["ties", "tie length"]),
    ("cover 0.04", with_(cover=0.04), ["cover"]),
    ("bars start 20 cm higher (lap 0.40)", with_(bottom=GB_TOP + 0.20), ["level", "lap", "column concrete"]),
    ("top bends 0.10", with_(bend=0.10), ["bars", "rebar length"]),
    ("plate 0.15 wide", with_(plate=0.15), ["plate"]),
    ("no plate gap (bars to the top)", with_(pt=0.0001), ["plate", "bars", "column concrete"]),
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
        print(f"{'caught ' if hit else 'WRONG  '} {name}: {msg.splitlines()[0][:100]} | {msg.splitlines()[-1][:90]}")
        problems += not hit

build_columns()
print("control:", selfcheck()[-90:])
n0 = len(_coll(C_COL).objects)
build_columns()
assert len(_coll(C_COL).objects) == n0, "re-run duplicated objects"
print("shared data:", sorted({o.data.name for o in _coll(C_COL).objects if o.data}))
print(f"TESTS DONE problems: {problems}")
assert problems == 0
