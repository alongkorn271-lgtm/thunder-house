# Sales model -> compact JSON (triangles, mm, one colour per object) for the web viewer. Never saves the .blend.
#     OUT=sales.json blender -b KK01_KohKha_House.blend -P export_sales_json.py
import os, json, bpy, bmesh
OUT = os.environ["OUT"]
SKIP_COLS = {"KK01 Site"}
dg = bpy.context.evaluated_depsgraph_get()


def colour(o):
    m = o.active_material
    if not m:
        return "#cfcfcf"
    c = m.diffuse_color
    if m.node_tree:
        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b and not b.inputs["Base Color"].is_linked:
            c = b.inputs["Base Color"].default_value
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(x ** (1 / 2.2) * 255)))) for x in c[:3])


parts = []
for o in bpy.data.objects:
    if o.type != "MESH" or o.hide_render or "CPAC_Tiles" in o.name or any(c.name in SKIP_COLS for c in o.users_collection):
        continue
    bm = bmesh.new()
    bm.from_object(o, dg)
    bm.transform(o.matrix_world)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.verts.index_update()
    v = [int(round(x * 1000)) for vt in bm.verts for x in vt.co]
    f = [vt.index for fc in bm.faces for vt in fc.verts]
    bm.free()
    if not f:
        continue
    col = o.users_collection[0].name if o.users_collection else ""
    parts.append(dict(n=o.name, g=col, c=colour(o), v=v, f=f,
                      roof=o.name.startswith(("Roof", "Porch_Ceiling")),
                      t=(o.data.get("th") if hasattr(o.data, "get") else "") or ""))
json.dump(dict(parts=parts), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("SALES PARTS", len(parts), os.path.getsize(OUT) // 1024, "KB")
