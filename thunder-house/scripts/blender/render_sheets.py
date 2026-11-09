# Presentation renders for the drawing sheets (EEVEE + Freestyle outlines). Never saves the .blend.
#     blender -b ../KK01_Construction.blend -P render_sheets.py -- <out_dir> [shot ...]
# Each shot: stages shown in real materials ("show"), earlier stages ghosted white ("ghost"),
# optional rebar view (concrete of the shown stages made translucent), optional explode offsets, camera.
import sys, os, math
import bpy
from mathutils import Vector

a = sys.argv[sys.argv.index("--") + 1:]
OUT = os.path.abspath(a[0])
ONLY = set(a[1:])
os.makedirs(OUT, exist_ok=True)

COL = {k: f"KK01 {k} {v}" for k, v in (("ST00", "Grid"), ("ST01", "Footings"), ("ST02", "Stubs"), ("ST03", "Ground beams"),
       ("ST04", "Floor"), ("ST05", "Columns"), ("ST06", "Walls"), ("ST07", "Roof frame"), ("ST08", "Roof cover"),
       ("ST09", "Ceilings"), ("ST10", "Paint"), ("ST11", "Tiles"), ("ST12", "Electrical"), ("ST12b", "Conduit"),
       ("ST14", "Units"), ("ST16", "Sanitary"), ("ST18", "Extras"), ("ST20", "Furniture"))}
ORDER = list(COL)
STRUCT = {"ST01", "ST02", "ST03", "ST04", "ST05", "ST06"}
SKIP_EL = {"excavation"}
CX, CY = 6.5, 5.6            # plan centre of the house

sc = bpy.context.scene
# ---------------- look ----------------
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1800, 1200, 100
sc.render.film_transparent = False
try:
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
ee = sc.eevee
for k, v in (("taa_render_samples", 64), ("use_raytracing", True), ("use_shadows", True), ("shadow_ray_count", 2),
             ("use_gtao", True)):
    try:
        setattr(ee, k, v)
    except Exception:
        pass
w = sc.world or bpy.data.worlds.new("W")
sc.world = w
w.use_nodes = True
bg = w.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.96, 0.97, 0.98, 1)
bg.inputs[1].default_value = 0.42
sd = bpy.data.lights.new("Sun", "SUN")
sd.energy, sd.angle = 4.6, math.radians(2)
sun = bpy.data.objects.new("Sun", sd)
sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(52), 0, math.radians(-28))
# Freestyle: thin dark outlines like a technical illustration
sc.render.use_freestyle = True
sc.render.line_thickness_mode = "ABSOLUTE"
sc.render.line_thickness = 1.4
vl = sc.view_layers[0]
vl.use_freestyle = True
fs = vl.freestyle_settings
fs.crease_angle = math.radians(140)
ls = fs.linesets[0] if fs.linesets else fs.linesets.new("L")
ls.select_by_visibility, ls.visibility = True, "VISIBLE"
ls.select_silhouette = ls.select_border = ls.select_crease = True
ls.linestyle.color = (0.16, 0.18, 0.21)
ls.linestyle.thickness = 1.3
ls.linestyle.alpha = 1.0


def mat(name, rgb, rough=0.8, alpha=1.0, metal=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Alpha"].default_value = alpha
    if alpha < 1:
        try:
            m.surface_render_method = "BLENDED"
        except Exception:
            m.blend_method = "BLEND"
    return m


M_GHOST = mat("M_SheetGhost", (0.97, 0.97, 0.96), 0.9)
M_GLASSY = mat("M_SheetGlassy", (0.72, 0.80, 0.88), 0.35, alpha=0.07)
M_GROUND = mat("M_SheetGround", (0.80, 0.81, 0.79), 0.95)
M_GRASS = mat("M_SheetGrass", (0.50, 0.62, 0.38), 0.95)
M_ROOF = mat("M_SheetRoofTile", (0.20, 0.22, 0.25), 0.6)
M_GROUND_DK = mat("M_SheetGroundDk", (0.62, 0.64, 0.63), 0.95)
# accent colour for the concrete of the stage being presented (colour code per stage)
ACCENT = {"ST01": (0.36, 0.52, 0.70), "ST02": (0.34, 0.60, 0.52), "ST03": (0.52, 0.45, 0.72), "ST04": (0.78, 0.66, 0.42),
          "ST05": (0.78, 0.45, 0.38), "ST06": (0.30, 0.45, 0.62)}
M_ACC = {k: mat("M_SheetAcc_" + k, v, 0.7) for k, v in ACCENT.items() if v}
ACC_EL = {"concrete", "precast"}
M_REBAR = bpy.data.materials.get("M_Rebar")
# rebar a bit brighter so it reads against the translucent concrete
if M_REBAR and M_REBAR.node_tree:
    b = next(n for n in M_REBAR.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (0.62, 0.24, 0.08, 1)
    b.inputs["Roughness"].default_value = 0.45

# freeze the original state of every object
OBJS = {}
for st, cn in COL.items():
    c = bpy.data.collections.get(cn)
    if not c:
        continue
    for o in c.all_objects:
        if o.type not in ("MESH", "CURVE"):
            continue
        el = o.data.get("element") if hasattr(o.data, "get") else None
        OBJS[o.name] = dict(o=o, st=st, el=el, loc=o.location.copy(), hr=o.hide_render,
                            mats=[s.material for s in o.material_slots], links=[s.link for s in o.material_slots])
for o in bpy.data.objects:
    if o.type in ("MESH", "CURVE") and o.name not in OBJS and o.name not in ("Sun",):
        o.hide_render = True                       # loose helpers / other scenes


BEVEL = {}
for d in OBJS.values():
    if d["o"].type == "CURVE":
        BEVEL[d["o"].data.name] = d["o"].data.bevel_depth


def reset():
    for c in bpy.data.curves:
        if c.name in BEVEL:
            c.bevel_depth = BEVEL[c.name]
    for d in OBJS.values():
        o = d["o"]
        o.location = d["loc"]
        o.hide_render = d["hr"]
        for s, m, l in zip(o.material_slots, d["mats"], d["links"]):
            s.link = l
            if l == "OBJECT":
                s.material = m


def override(o, m):
    if not o.material_slots:
        o.data.materials.append(None) if hasattr(o.data, "materials") else None
    for s in o.material_slots:
        s.link = "OBJECT"
        s.material = m


ground = None


def set_ground(kind):
    global ground
    if ground:
        bpy.data.objects.remove(ground, do_unlink=True)
        ground = None
    if not kind:
        return
    z = {"pit": -1.72, "gl": -0.002, "dark": -1.72}[kind]
    me = bpy.data.meshes.new("SheetGround")
    r = 60
    me.from_pydata([(CX - r, CY - r, z), (CX + r, CY - r, z), (CX + r, CY + r, z), (CX - r, CY + r, z)], [], [(0, 1, 2, 3)])
    me.materials.append({"gl": M_GRASS, "pit": M_GROUND, "dark": M_GROUND_DK}.get(kind, M_GROUND))
    ground = bpy.data.objects.new("SheetGround", me)
    sc.collection.objects.link(ground)


def camera(direction, target, scale, ortho=True, lens=40):
    cd = bpy.data.cameras.get("SheetCam") or bpy.data.cameras.new("SheetCam")
    cam = bpy.data.objects.get("SheetCam") or bpy.data.objects.new("SheetCam", cd)
    if cam.name not in sc.collection.objects:
        sc.collection.objects.link(cam)
    t = Vector(target)
    d = Vector(direction).normalized()
    cam.location = t + d * 60 if ortho else t + Vector(direction)
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    cd.type = "ORTHO" if ortho else "PERSP"
    cd.ortho_scale, cd.lens, cd.clip_start, cd.clip_end = scale, lens, 0.05, 300
    sc.camera = cam


ISO = (-1.0, -1.25, 0.95)        # from the front-left, like the A-sheets


def shot(name, show, ghost=(), rebar=False, explode=None, ground="pit", cam=None, hide_el=(), only_el=None, res=None, accent=True, lines=True, glassy=(), tile=True):
    if ONLY and name not in ONLY:
        return
    reset()
    set_ground(ground)
    vis = set(show) | set(ghost)
    for d in OBJS.values():
        o, st, el = d["o"], d["st"], d["el"]
        if st not in vis or d["hr"] or st == "ST00" or el in SKIP_EL or el in hide_el:
            o.hide_render = True
            continue
        if only_el is not None and st in show and el not in only_el and o.type != "CURVE":
            o.hide_render = True
            continue
        o.hide_render = False
        if st in ghost:
            if o.type == "CURVE":
                o.hide_render = True                  # no ghost rebar
            else:
                override(o, M_GHOST)
        elif st in STRUCT and o.type == "CURVE" and not rebar:
            o.hide_render = True                      # rebar only in rebar shots
        elif rebar and o.type == "MESH" and st in STRUCT:
            override(o, M_GLASSY)
        elif el in glassy and o.type == "MESH":
            override(o, M_GLASSY)
        elif tile and el == "tile_bed":
            override(o, M_ROOF)
        elif accent and st in M_ACC and el in ACC_EL and o.type == "MESH":
            override(o, M_ACC[st])
        if rebar and o.type == "CURVE" and not o.hide_render and o.data.name in BEVEL:
            o.data.bevel_depth = BEVEL[o.data.name] * 1.7
        if explode and st in explode:
            o.location = d["loc"] + Vector((0, 0, explode[st]))
    camera(*(cam or (ISO, (CX, CY, 0.0), 21.0)))
    if res:
        sc.render.resolution_x, sc.render.resolution_y = res
    else:
        sc.render.resolution_x, sc.render.resolution_y = 1800, 1200
    sc.render.use_freestyle = lines and not rebar
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", sc.render.filepath, flush=True)


ALL = ORDER[1:]
# cover: the finished house + the structural system exploded
shot("cover_house", ALL, ground="gl", cam=(ISO, (CX, CY, 1.4), 19.0), accent=False, lines=False)
shot("cover_exploded", ["ST01", "ST02", "ST03", "ST04", "ST05", "ST07"],
     explode={"ST01": 0, "ST02": 0, "ST03": 1.6, "ST04": 3.0, "ST05": 4.6, "ST07": 7.0},
     ground="pit", cam=(ISO, (CX, CY, 2.6), 27.0), res=(1500, 1800))
# one presentation image per stage: the stage in colour, everything earlier in white
STAGE_CAM = {"ST01": (ISO, (CX, CY, -1.2), 20.0), "ST02": (ISO, (CX, CY, -0.8), 20.0), "ST03": (ISO, (CX, CY, -0.5), 20.0),
             "ST04": (ISO, (CX, CY, -0.2), 20.0), "ST05": (ISO, (CX, CY, 1.2), 21.0), "ST06": (ISO, (CX, CY, 1.2), 21.0)}
prev = []
for st in ["ST01", "ST02", "ST03", "ST04", "ST05", "ST06"]:
    shot(f"{st}_stage", [st], ghost=prev, ground="pit", cam=STAGE_CAM[st])
    prev.append(st)
# rebar close-ups (concrete translucent)
shot("ST01_rebar", ["ST01"], rebar=True, ground="dark", cam=((-4.0, -5.5, 3.6), (4.25, 7.5, -1.45), 0, False, 40), res=(1500, 1100))
shot("ST02_rebar", ["ST01", "ST02"], rebar=True, ground="dark", cam=((-3.6, -5.0, 2.6), (4.25, 7.5, -0.7), 0, False, 40), res=(1500, 1100))
shot("ST03_rebar", ["ST02", "ST03"], rebar=True, ground="dark", cam=((-3.2, -4.4, 2.6), (5.0, 7.5, 0.4), 0, False, 40), res=(1500, 1100))
shot("ST04_rebar", ["ST03", "ST04"], rebar=True, ground="dark", cam=((-3.0, -4.2, 3.4), (2.2, 4.0, 0.6), 0, False, 36), res=(1500, 1100))
shot("ST05_rebar", ["ST03", "ST05"], rebar=True, ground="dark", cam=((-3.6, -4.8, 2.8), (5.0, 7.5, 2.2), 0, False, 36), res=(1500, 1100))
shot("ST06_rebar", ["ST06"], ghost=["ST03", "ST04", "ST05"], glassy={"brick", "plaster"}, ground="pit",
     cam=((-5.5, -7.5, 4.0), (4.5, 2.0, 1.8), 0, False, 30), res=(1500, 1100))

# ---------------- ST07 onward ----------------
S16 = ["ST01", "ST02", "ST03", "ST04", "ST05", "ST06"]
BACK = (1.0, 1.25, 0.95)
P = lambda off, tgt, lens: (off, tgt, 0, False, lens)
shot("ST07_stage", ["ST07"], ghost=S16, cam=(ISO, (CX, CY, 2.4), 22.5))
shot("ST07_detail", ["ST07"], ghost=["ST05", "ST06"], cam=P((-5.5, -8.0, 4.2), (6.8, 3.0, 4.6), 32), res=(1500, 1100))
shot("ST08_stage", ["ST07", "ST08"], ghost=S16, cam=(ISO, (CX, CY, 2.4), 22.5), accent=False)
shot("ST08_detail", ["ST07", "ST08"], ghost=S16, cam=(BACK, (CX, CY, 2.4), 22.5), accent=False, res=(1500, 1100))
shot("ST09_stage", ["ST09"], ghost=S16, cam=(ISO, (CX, CY, 1.8), 21.5), accent=False)
shot("ST09_detail", ["ST09"], ghost=["ST05"], glassy={"ceiling", "soffit"}, cam=P((-4.5, -6.5, 4.0), (5.5, 5.0, 3.4), 32), accent=False, res=(1500, 1100))
shot("ST10_stage", ["ST10"], ghost=["ST01", "ST02", "ST03", "ST04", "ST05"], cam=(ISO, (CX, CY, 1.4), 21.0), accent=False, lines=False)
shot("ST10_detail", ["ST10"], ghost=["ST01", "ST02", "ST03", "ST04", "ST05"], cam=(BACK, (CX, CY, 1.4), 21.0), accent=False, lines=False, res=(1500, 1100))
shot("ST11_stage", ["ST11"], ghost=["ST01", "ST02", "ST03", "ST04", "ST05"], cam=(ISO, (CX, CY, 0.4), 20.0), accent=False, lines=False)
shot("ST11_detail", ["ST11"], ghost=["ST03", "ST04", "ST05", "ST06"], cam=P((-3.5, -4.5, 2.4), (7.2, -0.4, 0.4), 34), accent=False, lines=False, res=(1500, 1100))
shot("ST12_stage", ["ST12", "ST12b"], ghost=["ST04", "ST05", "ST06"], cam=(ISO, (CX, CY, 1.8), 21.5), accent=False)
shot("ST12_detail", ["ST12", "ST12b", "ST06"], ghost=["ST04", "ST05"], glassy={"brick", "plaster"}, cam=P((-5.0, -6.5, 4.0), (6.0, 5.5, 2.4), 30), accent=False, res=(1500, 1100))
shot("ST14_stage", ["ST14"], ghost=["ST03", "ST04", "ST05", "ST06"], cam=(ISO, (CX, CY, 1.4), 21.0), accent=False)
shot("ST14_detail", ["ST06", "ST10", "ST11", "ST14"], ghost=["ST03", "ST04", "ST05"], cam=P((-1.5, -15.0, 1.2), (6.5, 0.0, 2.0), 32), accent=False, lines=False, res=(1500, 1100))
shot("ST16_stage", ["ST16"], ghost=S16, cam=(ISO, (CX, CY + 0.8, -0.2), 23.0), accent=False)
shot("ST16_detail", ["ST16", "ST06"], ghost=["ST04", "ST05"], glassy={"brick", "plaster"}, cam=P((-3.2, -4.0, 2.6), (1.4, 3.4, 1.2), 30), accent=False, res=(1500, 1100))
shot("ST18_stage", ["ST18"], ghost=S16 + ["ST11"], cam=(ISO, (CX, CY, 1.2), 21.5), accent=False, lines=False)
shot("ST18_detail", ["ST18", "ST10", "ST11"], ghost=S16, cam=P((-3.0, -5.0, 1.0), (7.15, 0.85, 2.0), 30), accent=False, lines=False, res=(1500, 1100))
shot("ST20_stage", ["ST20", "ST11", "ST14", "ST16"], ghost=["ST04", "ST05", "ST06"], cam=((-0.35, -0.75, 1.0), (CX, CY + 0.6, 0.8), 19.5), accent=False, lines=False)
shot("ST20_detail", ["ST20", "ST11", "ST14"], ghost=["ST04", "ST05", "ST06"], cam=((-2.6, -3.6, 5.2), (7.0, 4.9, 0.9), 0, False, 24), accent=False, lines=False, res=(1500, 1100))
print("ALL SHOTS DONE", flush=True)
