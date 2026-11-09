# ST12a mutation suite: devices with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st12.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
G = globals()
SPEC = {k: copy.deepcopy(G[k]) for k in ("EL", "EL_SOCKETS", "EL_SWITCHES", "EL_LIGHTS")}
ORIG = {k: G[k] for k in ("_el_light_at", "_el_wall", "_el_layout")}
problems = 0


def restore():
    for k, v in SPEC.items():
        if isinstance(G[k], dict):
            G[k].clear()
            G[k].update(copy.deepcopy(v))
        else:
            G[k][:] = copy.deepcopy(v)
    G.update(ORIG)


def sockets(i, new):
    def f():
        EL_SOCKETS[i] = new
        build_elec()
    return f


def drop_socket():
    del EL_SOCKETS[-1]
    build_elec()


def lights_unmoved():
    G["_el_light_at"] = lambda x, y, boards: (lambda r: ((x, y), r[1]) if r[0] else r)(ORIG["_el_light_at"](x, y, boards))
    build_elec()


def plate_off_wall():
    w = ORIG["_el_wall"]
    def g(boxes, x, y, h, size, flush=True, from_gl=False):
        b, side, base = w(boxes, x, y, h, size, flush, from_gl)
        ax, sg = side
        b = list(b)
        b[ax] += sg * 0.01
        b[ax + 3] += sg * 0.01
        return tuple(b), side, base
    G["_el_wall"] = g
    build_elec()


MUTATIONS = [
    ("bed-1 socket on the next wall", sockets(10, (4.70, 4.33, 0.40)), ["side"]),
    ("switches at +1.20", lambda: (EL.update(sw=1.20), build_elec()), ["height"]),
    ("downlights left on the runners", lights_unmoved, ["lights"]),
    ("trims inside the board", lambda: (EL.update(dl_below=-0.003), build_elec()), ["lights", "clash"]),
    ("a socket missing", drop_socket, ["count"]),
    ("flush boxes into the ties", lambda: (EL.update(margin=-0.07), build_elec()), ["tie"]),
    ("plates 1 cm off the wall", plate_off_wall, ["wall"]),
    ("FCU against the ceiling", lambda: (EL.update(fcu_gap=0.0), build_elec()), ["ac"]),
    ("socket back on door D3", sockets(21, (8.98, 2.40, 1.30)), ["opening", "tie", "wall"]),
]

for name, build, tags in MUTATIONS:
    try:
        build()
    except AssertionError as e:
        print(f"caught  {name}: builder refused ({str(e)[:80]})")
        restore()
        build_elec()
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

build_elec()
print("control:", selfcheck()[-150:])
n0 = len(_coll(C_ELEC).objects)
build_elec()
assert len(_coll(C_ELEC).objects) == n0, "re-run duplicated objects"
print(f"TESTS DONE problems: {problems}")
assert problems == 0
