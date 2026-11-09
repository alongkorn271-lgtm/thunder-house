# Print room rectangles, door/window boxes, fixtures and wall devices (input for the furniture layout).
import os, bpy
exec(open(os.path.join(os.path.dirname(bpy.data.filepath), "scripts", "kk01_load.py"), encoding="utf-8").read())
ob = _obstacles()
for name, seed, lvl, _ in ROOMS:
    try:
        r = _room_rect(seed, lvl - 0.3, ob)
        print("ROOM", name, [round(v, 3) for v in r])
    except AssertionError as e:
        print("ROOM", name, "open:", e)
for name, rect, _, _ in OPEN_ROOMS:
    print("OPEN", name, rect)


def bb(o):
    from mathutils import Vector
    vs = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [round(min(v[i] for v in vs), 2) for i in range(3)] + [round(max(v[i] for v in vs), 2) for i in range(3)]


for o in bpy.data.objects:
    n = o.name
    if (n.startswith("UN_") and n.endswith("_Frame")) or n.startswith(("EL_FCU", "EL_PB", "EL_WH", "SN_FX", "EL_SW")):
        print("OBJ", n, bb(o))
