# ST10 mutation suite: paint with one thing wrong, put the spec back, selfcheck must fail with its tag.
#     blender -b ../KK01_Construction.blend --python-exit-code 1 -P test_st10.py      (never saved)
import copy, os
import bpy

KK01_DIR = os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
G = globals()
SPEC = copy.deepcopy(PAINT)
ORIG = {k: G[k] for k in ("_seen_faces", "_film", "_paint_sources", "TILED_ROOMS", "_paint_layout")}
problems = 0


def restore():
    PAINT.clear()
    PAINT.update(copy.deepcopy(SPEC))
    G.update(ORIG)


def patch(**kw):
    def f():
        G.update(kw)
        build_paint()
    return f


def drop_face():
    full = ORIG["_seen_faces"]
    G["_seen_faces"] = lambda: full()[1:]
    build_paint()


def coat2_on_primer():
    film = ORIG["_film"]
    G["_film"] = lambda ax, sg, pl, p, k: film(ax, sg, pl, p, 2 if k == 3 else k)
    build_paint()


def no_board_cover():
    src = ORIG["_paint_sources"]
    def s():
        plaster, covers, opens, boards = src()
        return plaster, [c for c in covers if c[5] < 98.0], opens, boards
    G["_paint_sources"] = s
    build_paint()


def tiles_ignored():
    src = ORIG["_paint_sources"]
    tile = {tuple(round(v, 5) for v in b) for v in _ft_boxes().values() for b in v}
    def s():
        plaster, covers, opens, boards = src()
        return plaster, [c for c in covers if tuple(round(v, 5) for v in c) not in tile], opens, boards
    G["_paint_sources"] = s
    build_paint()
    G["_paint_sources"] = src


def no_ceiling_films():
    lay = ORIG["_paint_layout"]
    def l():
        d = lay()
        d["ceil_paint"] = d["ceil_paint"][:-3]
        return d
    G["_paint_layout"] = l
    build_paint()


def coat2_row():
    build_paint()
    bpy.data.objects["PT_Coat2"].data["element"] = "paint"


MUTATIONS = [
    ("a seen face left unprimed", drop_face, ["primer"]),
    ("paint run behind the tiles", tiles_ignored, ["primer"]),
    ("coat 2 laid on the primer (behind coat 1)", coat2_on_primer, ["coat2"]),
    ("outside walls painted above the soffit", no_board_cover, ["primer", "coat1"]),
    ("films 0.5 mm thick", lambda: (PAINT.update(film_t=0.0005), build_paint()), ["primer"]),
    ("ceiling films missing", no_ceiling_films, ["ceilings"]),
    ("coat 2 carries a take-off row", coat2_row, ["coat2"]),
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

build_paint()
print("control:", selfcheck()[-110:])
n0 = len(_coll(C_PAINT).objects)
build_paint()
assert len(_coll(C_PAINT).objects) == n0, "re-run duplicated objects"
print(f"TESTS DONE problems: {problems}")
assert problems == 0
