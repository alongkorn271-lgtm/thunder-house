# Build the KK01 construction model from an empty Blender, stage by stage, each stage checked as it lands:
#     blender -b --factory-startup --python-exit-code 1 -P build_kk01.py
# Saves ../KK01_Construction.blend (or $KK01_OUT).
import os, time
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
KK01_DIR = HERE
exec(open(os.path.join(HERE, "kk01_load.py"), encoding="utf-8").read())

for o in list(bpy.data.objects):   # factory startup cube/camera/light
    bpy.data.objects.remove(o)
bpy.context.scene.unit_settings.system = "METRIC"

BUILD_STAGES = (
    ("ST00 grid + ST01 footings", lambda: (build_grid(), build_footings()), selfcheck),
    ("ST02 stubs", build_stubs, selfcheck),
    ("ST03 ground beams", build_ground_beams, selfcheck),
    ("ST04 floor", build_floor, selfcheck),
    ("ST05 columns", build_columns, selfcheck),
    ("ST06 walls", build_walls, selfcheck),
    ("ST07 roof frame", build_roof_frame, selfcheck),
    ("ST08 roof cover", build_roof_cover, selfcheck),
    ("ST09 ceilings", build_ceilings, selfcheck),
    ("ST11 tiles (before the paint: it stops at them)", build_tiles, selfcheck),
    ("ST10 paint", build_paint, selfcheck),
    ("ST12a electrical devices", build_elec, selfcheck),
    ("ST12b circuits, conduit, wire", build_conduit, selfcheck),
    ("ST14 doors, windows", build_units, selfcheck),
    ("ST16 sanitary + fixtures", build_sanitary, selfcheck),
    ("ST18 extras (cladding, arches, screens, yard, beads, trims)", build_extras, selfcheck),
)
t0 = time.time()
for name, build, check in BUILD_STAGES:
    build()
    print(f"[{time.time() - t0:5.1f} s] {name}: {check()}")
print(report())
print(report(C_STUB))
print(report(C_GB))
print(floor_report())
print(report(C_COL))
print(walls_report())
print(roof_report())
print(cover_report())
print(ceiling_report())
print(tiles_report())
print(paint_report())
print(elec_report())
print(conduit_report())
print(units_report())
print(sanitary_report())
print(extras_report())
out = os.environ.get("KK01_OUT") or os.path.join(HERE, "..", "KK01_Construction.blend")
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
print("BUILD DONE", os.path.abspath(out))
