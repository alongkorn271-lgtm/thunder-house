# ST16 mutation suite: sanitary with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st16.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
G = globals()
SPEC = {k: copy.deepcopy(G[k]) for k in ("SN",)}
ORIG = {k: G[k] for k in ("_sn_layout",)}
FIX = list(SN_FIX)
problems = 0


def restore():
    SN.clear()
    SN.update(copy.deepcopy(SPEC["SN"]))
    SN_FIX[:] = FIX
    G.update(ORIG)


def layout(edit):
    def f():
        lay = ORIG["_sn_layout"]
        def l():
            d = lay()
            edit(d)
            return d
        G["_sn_layout"] = l
        build_sanitary()
        G["_sn_layout"] = lay
    return f


def drop_wc_cw(d):
    pts = d["pipes"][("CW", "1/2")]
    k = next(i for i, p in enumerate(pts) if abs(p[-1][0] - 1.44) < 1e-6 and abs(p[-1][2] - (FL_WET + 0.20)) < 1e-6)
    del pts[k]


def reverse_grey(d):
    d["pipes"][("W", "2")][0] = d["pipes"][("W", "2")][0][::-1]


def riser_in_column(d):
    p = d["pipes"][("S", "4")][0]
    d["pipes"][("S", "4")][0] = [(0.0, 4.0, z) for _, _, z in p[:2]] + p[2:]


def tank_up():
    SN["tank"]["top"] = 0.10
    build_sanitary()


MUTATIONS = [
    ("septic tanks 10 cm out of the ground", tank_up, ["struct", "grade"]),
    ("soil laid at 1:100", lambda: (SN.update(slope_s=1 / 100), build_sanitary()), ["grade", "connect"]),
    ("water main 10 cm deep", lambda: (SN.update(cw_z=-0.10), build_sanitary()), ["cover", "gap"]),
    ("the bath 1 WC stub left out", layout(drop_wc_cw), ["connect"]),
    ("a grey line laid against the flow", layout(reverse_grey), ["grade"]),
    ("the bath 1 WC riser through column E1", layout(riser_in_column), ["clash", "connect"]),
    ("vents 1 m under the eave", lambda: (globals().update(_sn_vent=None), SN.update(), build_sanitary()) if False else layout(lambda d: d["pipes"][("V", "2")].__setitem__(0, [d["pipes"][("V", "2")][0][0], (d["pipes"][("V", "2")][0][0][0], d["pipes"][("V", "2")][0][0][1], 3.50)]))(), ["vent"]),
    ("a WC missing", lambda: (SN_FIX.__setitem__(slice(None), [f for f in FIX if f[0] != "B2_WC"]), build_sanitary()), ["fixtures", "connect"]),
    ("water 5 cm higher: on the soil pipe", lambda: (SN.update(cw_z=-0.40), build_sanitary()), ["gap"]),
]

for name, build, tags in MUTATIONS:
    try:
        build()
    except AssertionError as e:
        print(f"caught  {name}: builder refused ({str(e)[:80]})")
        restore()
        build_sanitary()
        continue
    except Exception as e:
        print(f"caught  {name}: builder failed ({type(e).__name__}: {str(e)[:60]})")
        restore()
        build_sanitary()
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

build_sanitary()
print("control:", selfcheck()[-120:])
n0 = len(_coll(C_SAN).objects)
build_sanitary()
assert len(_coll(C_SAN).objects) == n0, "re-run duplicated objects"
print(f"TESTS DONE problems: {problems}")
assert problems == 0
