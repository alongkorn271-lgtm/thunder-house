# Export a stage-by-stage construction model to compact JSON (mm integers): boxes where an object is boxes,
# triangles otherwise, polylines for curves (structural rebar flagged rb=1).
#     OUT=model.json [MODEL_SCRIPTS=<project>/Construction/scripts] blender -b <Construction.blend> -P export_model_json.py
# Needs the project's loader (kk01_load.py: _world_bm, _obj_boxes, _world_bars, C_* collection names) from the
# stage-by-stage build (build_kk01.py). Edit LAYERS for another project's collections / labels.
import os, json, bpy, bmesh
KK01_DIR = os.environ.get("MODEL_SCRIPTS") or os.path.join(os.path.dirname(bpy.data.filepath), "scripts")
exec(open(os.path.join(KK01_DIR, "kk01_load.py"), encoding="utf-8").read())
OUT = os.environ["OUT"]
SKIP_EL = {"excavation", "paint", "grout", "adhesive", "membrane", "screed", "tile_bed", "opening", "hanger", "rod_x"}
LAYERS = [(C_FOOT, "ST01 ฐานราก"), (C_STUB, "ST02 ตอม่อ"), (C_GB, "ST03 คานคอดิน"), (C_FLOOR, "ST04 พื้น"), (C_COL, "ST05 เสา"),
          (C_WALL, "ST06 ผนัง + ฉาบ"), (C_ROOF, "ST07 โครงหลังคา"), (C_COVER, "ST08 มุงหลังคา"), (C_CEIL, "ST09 ฝ้า"),
          (C_PAINT, "ST10 สี"), (C_TILE, "ST11 กระเบื้อง + บันได"), (C_ELEC, "ST12 อุปกรณ์ไฟฟ้า"), (C_COND, "ST12 ท่อร้อยสายไฟ"),
          (C_UNIT, "ST14 ประตูหน้าต่าง"), (C_SAN, "ST16 สุขาภิบาล"), (C_EXTRA, "ST18 รายการย่อย"),
          ("KK01 ST20 Furniture", "ST20 เฟอร์นิเจอร์")]
mm = lambda v: int(round(v * 1000))


def col_of(o):
    m = o.active_material or (o.data.materials[0] if getattr(o.data, "materials", None) and len(o.data.materials) else None)
    if not m:
        return "#9aa3ab"
    c = m.diffuse_color
    if m.node_tree:
        b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if b:
            c = b.inputs["Base Color"].default_value
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(round(x ** (1 / 2.2) * 255)))) for x in c[:3])


parts = []
stats = {}
for li, (cn, label) in enumerate(LAYERS):
    c = bpy.data.collections.get(cn)
    if not c:
        continue
    for o in c.objects:
        if o.hide_render or o.data is None:
            continue
        el = o.data.get("element") if hasattr(o.data, "get") else None
        if cn == C_PAINT and o.name not in ("PT_Coat2", "PT_CeilPaint"):
            continue                                            # paint: the outer coats only
        if el in SKIP_EL and not (cn == C_PAINT) and not (cn == C_COVER and el == "tile_bed"):
            continue
        rec = dict(n=o.name, L=li, t=(o.data.get("th") if hasattr(o.data, "get") else "") or "", e=el or "", c=col_of(o))
        if o.type == "CURVE":
            pts = []
            for sp in _world_bars(o):
                pts.append([mm(x) for p in sp for x in (p.x, p.y, p.z)])
            rec["p"] = pts
            rec["d"] = mm(o.data.bevel_depth * 2)
            if cn in (C_FOOT, C_STUB, C_GB, C_FLOOR, C_COL, C_WALL):
                rec["rb"] = 1
        elif o.type == "MESH":
            bm = _world_bm(o)
            try:
                try:
                    bx = _obj_boxes(bm, o.name)
                    rec["b"] = [mm(v) for b in bx for v in b]
                except Exception:
                    bmesh.ops.triangulate(bm, faces=bm.faces[:])
                    bm.verts.index_update()
                    rec["v"] = [mm(x) for v in bm.verts for x in v.co]
                    rec["f"] = [v.index for f in bm.faces for v in f.verts]
            finally:
                bm.free()
        else:
            continue
        parts.append(rec)
        stats[label] = stats.get(label, 0) + 1
json.dump(dict(layers=[l for _, l in LAYERS], parts=parts), open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("PARTS", len(parts), "SIZE", os.path.getsize(OUT) // 1024, "KB")
print(stats)
