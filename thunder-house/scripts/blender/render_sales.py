# Sales-model views with furniture (never saves the .blend):
#     blender -b KK01_KohKha_House.blend -P render_sales.py -- <out_dir> [shot ...]
# Uses the sales model's own materials / lighting; the roof is hidden for the doll-house views.
import sys, os, math
import bpy
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(a[0]); ONLY = set(a[1:])
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene
ROOF = [o for o in bpy.data.objects if o.name.startswith(("Roof", "Porch_Ceiling"))]


def cam(name, loc, tgt, lens=24, ortho=None):
    cd = bpy.data.cameras.new(name)
    if ortho:
        cd.type, cd.ortho_scale = "ORTHO", ortho
    cd.lens, cd.clip_start, cd.clip_end = lens, 0.05, 400
    o = bpy.data.objects.new(name, cd)
    sc.collection.objects.link(o)
    o.location = Vector(loc)
    o.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    return o


def shot(name, camera, roof=False, res=(1800, 1200)):
    if ONLY and name not in ONLY:
        return
    for o in ROOF:
        o.hide_render = not roof
    sc.camera = camera
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = *res, 100
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath, flush=True)


C = (6.5, 5.6, 0.8)
d = Vector((-0.55, -0.85, 1.0)).normalized() * 60
shot("sales_dollhouse", cam("C_Doll", Vector(C) + d, C, ortho=19.5))
shot("sales_exterior", cam("C_Ext", (-9.0, -11.5, 4.2), (6.5, 5.0, 2.2), lens=28), roof=True)
shot("sales_living", cam("C_Liv", (9.15, 2.0, 1.7), (5.6, 5.4, 1.2), lens=18), roof=True, res=(1500, 1100))
shot("sales_bed1", cam("C_Bed1", (4.6, 7.2, 1.7), (1.8, 4.6, 1.0), lens=18), roof=True, res=(1500, 1100))
shot("sales_kitchen", cam("C_Kit", (9.2, 9.5, 1.7), (4.2, 11.5, 1.1), lens=18), roof=True, res=(1500, 1100))
print("ALL SALES SHOTS DONE", flush=True)
