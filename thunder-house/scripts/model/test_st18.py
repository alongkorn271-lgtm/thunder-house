# ST18 mutation suite: extras with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st18.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
G = globals()
SPEC = copy.deepcopy(EX)
ORIG = {k: G[k] for k in ("_ex_layout",)}
problems = 0


def restore():
    EX.clear()
    EX.update(copy.deepcopy(SPEC))
    G.update(ORIG)


def layout(edit):
    def f():
        lay = ORIG["_ex_layout"]
        def l():
            d = lay()
            edit(d)
            return d
        G["_ex_layout"] = l
        build_extras()
        G["_ex_layout"] = lay
    return f


MUTATIONS = [
    ("battens @10 cm", lambda: (EX.update(pitch=0.10), build_extras()), ["clad"]),
    ("battens 3 cm off the paint", lambda: (EX.update(off=0.03), build_extras()), ["clad"]),
    ("a shower screen left out", layout(lambda d: d["screen"].pop()), ["screen"]),
    ("the yard at +0.20", lambda: (EX.update(yard_top=0.20), build_extras()), ["yard"]),
    ("no lid opening over the septic tank", lambda: (EX.update(lid=0.001), build_extras()), ["yard"]),
    ("the yard onto the laundry steps", lambda: (EX.update(yard=(10.66, 9.36, 13.13, 11.60)), build_extras()), ["yard"]),
]

for name, build, tags in MUTATIONS:
    try:
        build()
    except AssertionError as e:
        print(f"caught  {name}: builder refused ({str(e)[:80]})")
        restore()
        build_extras()
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

build_extras()
print("control:", selfcheck()[-120:])
n0 = len(_coll(C_EXTRA).objects)
build_extras()
assert len(_coll(C_EXTRA).objects) == n0, "re-run duplicated objects"
print(f"TESTS DONE problems: {problems}")
assert problems == 0
