# ST12b mutation suite: conduit with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st12b.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
G = globals()
SPEC = {k: copy.deepcopy(G[k]) for k in ("EC", "LT_LANE")}
ORIG = {k: G[k] for k in ("_cd_layout", "_fillet", "_cd_hard")}
CIRC = copy.deepcopy(CIRCUITS)
problems = 0


def restore():
    for k, v in SPEC.items():
        G[k].clear()
        G[k].update(copy.deepcopy(v))
    CIRCUITS[:] = copy.deepcopy(CIRC)
    G.update(ORIG)


def layout(edit):
    def f():
        lay = ORIG["_cd_layout"]
        def l():
            d = lay()
            edit(d)
            return d
        G["_cd_layout"] = l
        build_conduit()
    return f


def drop_branch(d):
    k = next(i for i, r in enumerate(d["runs"]) if r.get("dev") == "EL_SO_16")
    del d["runs"][k]


def lower_run(d):
    r = next(r for r in d["runs"] if r.get("dev") == "EL_SO_25")
    r["pts"] = [(p[0], p[1], p[2] - 0.20) if p[2] > 3.7 else p for p in r["pts"]]


def same_lane():
    LT_LANE["L2"] = EC["lt_z"]
    build_conduit()


def no_hard():
    G["_cd_hard"] = lambda: []
    build_conduit()


def drop_circuit():
    CIRCUITS[:] = [c for c in CIRCUITS if c[0] != "P4"]
    build_conduit()


MUTATIONS = [
    ("a socket branch missing", layout(drop_branch), ["connect"]),
    ("sharp corners (no bends)", lambda: (G.update(_fillet=lambda pts, r, step=0.015: [tuple(p) for p in pts]), build_conduit()), ["bend"]),
    ("bends at r 50 mm", lambda: (EC.update(r=0.05), build_conduit()), ["bend"]),
    ("a run dropped under the bed 2 ceiling", layout(lower_run), ["visible", "connect"]),
    ("L2 and P3 on one lane under the lean-to", same_lane, ["clash"]),
    ("holes through tie columns allowed", no_hard, ["tie"]),
    ("circuit P4 left out", drop_circuit, ["connect"]),
    ("all lanes 1 cm apart", lambda: (EC.update(lane_s=0.010), build_conduit()), ["clash"]),
]

for name, build, tags in MUTATIONS:
    try:
        build()
    except AssertionError as e:
        print(f"caught  {name}: builder refused ({str(e)[:80]})")
        restore()
        build_conduit()
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

build_conduit()
print("control:", selfcheck()[-150:])
n0 = len(_coll(C_COND).objects)
build_conduit()
assert len(_coll(C_COND).objects) == n0, "re-run duplicated objects"
print(f"TESTS DONE problems: {problems}")
assert problems == 0
