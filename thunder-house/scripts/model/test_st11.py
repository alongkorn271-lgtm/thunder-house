# ST11 mutation suite: tiles with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st11.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
G = globals()
SPEC = {k: copy.deepcopy(G[k]) for k in ("FT", "WP", "SHOWER", "FLOOR_ZONES", "STEPS")}
ORIG = {k: G[k] for k in ("_tiles_layout", "_risers", "_bath_faces", "_step_geom")}
problems = 0


def restore():
    for k, v in SPEC.items():
        G[k].clear()
        G[k].update(copy.deepcopy(v))
    G.update(ORIG)


def ft(tp, **kw):
    def f():
        FT[tp].update(kw)
        build_tiles()
    return f


def layout(edit):
    def f():
        lay = ORIG["_tiles_layout"]
        def l():
            d = lay()
            edit(d)
            return d
        G["_tiles_layout"] = l
        build_tiles()
    return f


def drop_tile(d):
    d["tiles"]["house"] = d["tiles"]["house"][:40] + d["tiles"]["house"][41:]


def no_risers(d):
    d["riser"], d["riser_bed"] = [], []


def short_walls(d):
    d["wall"] = [b for b in d["wall"] if b[5] < 3.0]


def bath_as_fl2():
    FLOOR_ZONES["bath2"] = "FL2"
    build_tiles()


def overlap_corner(d):
    d["wall"].append(d["wall"][0])


def step_tiles(key, keep):
    def edit(d):
        d["steps"][key] = d["steps"][key][:keep]
    return layout(edit)


def uneven_risers():
    sg = ORIG["_step_geom"]
    def g(nm):
        f, ax, E, s_, eps, r, h, c = sg(nm)
        h = list(h)
        h[2] += 0.03
        return f, ax, E, s_, eps, r, h, c
    G["_step_geom"] = g
    build_tiles()


def spare_off():
    G["SPARE"], old = 0.0, G["SPARE"]
    try:
        build_tiles()
    finally:
        G["SPARE"] = old


MUTATIONS = [
    ("FL2 joints 3 mm", ft("FL2", joint=0.003), ["joints"]),
    ("FL4 tiles 45×45", ft("FL4", size=(0.45, 0.45, 0.008)), ["size", "joints", "count"]),
    ("one house tile left out", layout(drop_tile), ["coverage"]),
    ("no riser tiles at the level changes", layout(no_risers), ["riser", "coverage"]),
    ("bath wall tiles stop under 3.00", layout(short_walls), ["wall"]),
    ("bath 2 floor laid in FL2 tiles", bath_as_fl2, ["zone", "level", "size", "joints", "coverage"]),
    ("FL3 tiles 1 cm thicker (tile proud of +0.70)", ft("FL3", size=(0.60, 0.60, 0.019)), ["level", "clash", "overlap"]),
    ("waterproofing 0.20 up the walls", lambda: (WP.update(up=0.20), build_tiles()), ["waterproof"]),
    ("shower bay moved off the W5 wall", lambda: (SHOWER.update(bath1=(1.5, 2.5)), build_tiles()), ["waterproof"]),
    ("a wall tile laid twice", layout(overlap_corner), ["overlap"]),
    ("no breakage allowance", spare_off, ["count"]),
    ("steps: tread 2 three cm high (uneven risers)", uneven_risers, ["steps", "clash", "overlap"]),
    ("steps: risers left bare", step_tiles("riser", 0), ["steps"]),
    ("steps: last tread tile missing", step_tiles("tread", 8), ["steps"]),
    ("steps: treads 0.22", lambda: (STEPS["flights"]["front"].update(treads=(0.22, 0.22, 0.22)), build_tiles()), ["steps"]),
    ("steps into the column G3", lambda: (STEPS["flights"]["front"].update(span=(5.0, 7.13)), build_tiles()), ["clash"]),
]

for name, build, tags in MUTATIONS:
    try:
        build()
    except AssertionError as e:
        print(f"caught  {name}: builder refused ({str(e)[:80]})")
        restore()
        build_tiles()
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

build_tiles()
print("control:", selfcheck()[-150:])
n0 = len(_coll(C_TILE).objects)
build_tiles()
assert len(_coll(C_TILE).objects) == n0, "re-run duplicated objects"
print(f"TESTS DONE problems: {problems}")
assert problems == 0
