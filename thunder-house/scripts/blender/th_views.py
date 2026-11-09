# -*- coding: utf-8 -*-
"""Interior-photo cameras + flat material-ID maps for AI image tools (thunder-house, own implementation).
Never saves the .blend.

    blender -b <house.blend> --python-exit-code 1 -P th_views.py -- <out_dir> <cameras.json> [--idmap] [--size 1080x1920]

cameras.json: [{"id": "02_living", "eye": [x, y, z], "look": [x, y], "lens": 18, "shift_y": -0.05}, ...]
  * the camera is always level (vertical lines stay vertical); framing up/down only through shift_y
  * eye z = floor + about 1.0 m; lens 16–24 mm in a 9:16 frame
Without --idmap: the normal render <id>.png with the file's own materials and lights.
With --idmap:    <id>_idmap.png — every surface one flat colour by material group, no light, no anti-alias blur —
                 plus legend.json (group → colour, description, materials). A groups.json next to cameras.json
                 ({"wood": ["teak", "my_door"], ...}) adds keywords that win over the built-in table.
"""
import bpy, sys, os, json, math, re
from mathutils import Vector

args = sys.argv[sys.argv.index("--") + 1:]
OUT, CAMS = os.path.abspath(args[0]), json.load(open(args[1], encoding="utf-8"))
IDMAP = "--idmap" in args
W, H = (int(v) for v in (args[args.index("--size") + 1] if "--size" in args else "1080x1920").split("x"))
os.makedirs(OUT, exist_ok=True)
sc = bpy.context.scene

# group: (colour, what it is, keywords matched against the material name, lower case)
GROUPS = {
    "glass":    ("#2196f3", "window glass, mirrors", ["glass", "mirror"]),
    "frame":    ("#283593", "window / door frames, trims, uPVC", ["alu", "frame", "trim", "upvc"]),
    "ceiling":  ("#26c6da", "ceiling boards", ["ceiling", "gypsum", "soffit_board"]),
    "walltile": ("#f06292", "wall tiles", ["wall_tile", "tile_w", "tilewall"]),
    "floor":    ("#ffeb3b", "floor tiles / floor finish", ["tile_fl", "floor", "screed", "vinyl"]),
    "wall":     ("#e53935", "plastered / painted walls, columns", ["wall", "plaster", "paint", "column", "soffit", "brick"]),
    "roof":     ("#8e24aa", "roof, fascia, roof void", ["roof", "fascia", "metalsheet", "valley"]),
    "wood":     ("#2e7d32", "wood: furniture, cabinets, doors", ["wood", "oak", "walnut", "teak", "door", "rattan"]),
    "fabric":   ("#aed581", "fabric: sofa, bedding, rugs, cushions", ["fabric", "linen", "cream", "taupe", "sage", "cognac", "jute", "rug", "f_white"]),
    "ceramic":  ("#fafafa", "ceramic sanitary ware", ["ceramic", "porcelain", "china"]),
    "stone":    ("#a1887f", "stone / worktops", ["stone", "granite", "marble", "quartz"]),
    "metal":    ("#616161", "black metal, appliances, fittings", ["metal", "steel", "black", "chrome", "stainless"]),
    "plant":    ("#76ff03", "plants", ["leaf", "plant", "foliage"]),
    "lamp":     ("#fff59d", "lamps, shades", ["lamp", "shade", "glow"]),
    "ground":   ("#827717", "lawn, garden", ["lawn", "grass", "ground"]),
    "concrete": ("#fb8c00", "concrete steps, plinth, paving, pots", ["concrete", "paver", "plinth", "terracotta", "pot"]),
    "other":    ("#9e9e9e", "everything else", []),
}


def level_camera(c):
    eye = Vector(c["eye"])
    look = Vector((c["look"][0], c["look"][1], eye.z))
    cd = bpy.data.cameras.new("TH_" + c["id"])
    cd.lens, cd.clip_start, cd.clip_end = c.get("lens", 20), 0.05, 500
    cd.shift_y = c.get("shift_y", 0.0)
    cd.sensor_fit = "AUTO"
    o = bpy.data.objects.new("TH_" + c["id"], cd)
    sc.collection.objects.link(o)
    o.location = eye
    yaw = math.atan2(look.y - eye.y, look.x - eye.x) - math.pi / 2
    o.rotation_euler = (math.pi / 2, 0.0, yaw)            # exactly level: X = 90°
    return o


def safe(i):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", str(i)):
        sys.exit(f"bad camera id {i!r}")
    return i


def classify():
    extra = {}
    gp = os.path.join(os.path.dirname(os.path.abspath(args[1])), "groups.json")
    if os.path.exists(gp):
        extra = json.load(open(gp, encoding="utf-8"))
    out = {}
    for m in bpy.data.materials:
        n = m.name.lower()
        g = next((g for g, kws in extra.items() if any(k.lower() in n for k in kws)), None)
        g = g or next((g for g, (_, _, kws) in GROUPS.items() if any(k in n for k in kws)), "other")
        out[m.name] = g
    return out


def to_lin(hx):
    return tuple(((int(hx[i:i + 2], 16) / 255) ** 2.2) for i in (1, 3, 5))


r = sc.render
r.resolution_x, r.resolution_y, r.resolution_percentage = W, H, 100
r.use_border = False
r.film_transparent = False
r.image_settings.file_format = "PNG"
if IDMAP:
    grp = classify()
    flat = {}
    for g, (hx, _, _) in GROUPS.items():
        fm = bpy.data.materials.new("TH_ID_" + g)
        fm.diffuse_color = (*to_lin(hx), 1)
        flat[g] = fm
    used = {}
    for o in bpy.data.objects:
        if o.type not in ("MESH", "CURVE") or o.hide_render:
            continue
        slots = o.material_slots
        if not slots:
            o.data.materials.append(flat["other"])
            used.setdefault("other", set()).add("(no material)")
            continue
        for s in slots:
            g = grp.get(s.material.name, "other") if s.material else "other"
            used.setdefault(g, set()).add(s.material.name if s.material else "(empty)")
            s.link = "OBJECT"
            s.material = flat[g]
    r.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light, sh.color_type = "FLAT", "MATERIAL"
    sh.show_shadows = sh.show_cavity = sh.show_object_outline = sh.show_specular_highlight = False
    sh.background_type, sh.background_color = "VIEWPORT", (0.1, 0.1, 0.1)
    sc.display.render_aa = "OFF"
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    legend = {g: dict(color=GROUPS[g][0], surface=GROUPS[g][1], materials=sorted(ms)) for g, ms in sorted(used.items())}
    json.dump(legend, open(os.path.join(OUT, "legend.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for c in CAMS:
    sc.camera = level_camera(c)
    r.filepath = os.path.join(OUT, safe(c["id"]) + ("_idmap" if IDMAP else "") + ".png")
    bpy.ops.render.render(write_still=True)
    print("RENDERED", r.filepath, flush=True)
if IDMAP:
    print("LEGEND", {g: v["color"] for g, v in legend.items()})
    if "other" in legend:
        print("OTHER (add to groups.json):", legend["other"]["materials"])
