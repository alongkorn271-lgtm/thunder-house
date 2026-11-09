# ST20 furniture (presentation only — NOT a construction stage, never counted in quantities).
#     blender -b KK01_Construction.blend --python-exit-code 1 -P scripts/kk01_furniture.py      (adds/replaces, then saves)
#     sales model: blender -b KK01_KohKha_House.blend -P kk01_furniture.py -- --collection "KK01 Furniture"
#     ... -P scripts/kk01_furniture.py -- --remove                                               (takes it out again)
# Collection "KK01 ST20 Furniture": toggle it to view the house with / without furniture.
# Layout from the model (q_rooms.py): room rectangles, doors, windows, AC units, fixtures — style: Furnishing/style_prompt.md
import sys, bpy, bmesh

C_FURN = sys.argv[sys.argv.index("--collection") + 1] if "--collection" in sys.argv else "KK01 ST20 Furniture"
FL = 0.80                                # finished floor (tile surface)

old = bpy.data.collections.get(C_FURN)
if old:
    for o in list(old.all_objects):
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(old)
if "--remove" in sys.argv:
    bpy.ops.wm.save_mainfile()
    print("FURNITURE REMOVED")
    raise SystemExit
col = bpy.data.collections.new(C_FURN)
bpy.context.scene.collection.children.link(col)


def mat(name, rgb, rough=0.7):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*rgb, 1)
    return m


M = dict(wood=mat("F_Wood", (0.50, 0.34, 0.21), 0.5), wood_l=mat("F_WoodLight", (0.72, 0.56, 0.38), 0.5),
         fabric=mat("F_Cream", (0.86, 0.82, 0.74), 0.9), taupe=mat("F_Taupe", (0.58, 0.52, 0.45), 0.9),
         sage=mat("F_Sage", (0.55, 0.60, 0.48), 0.8), terra=mat("F_Terracotta", (0.70, 0.40, 0.28), 0.8),
         leather=mat("F_Cognac", (0.55, 0.30, 0.15), 0.5), black=mat("F_Black", (0.05, 0.05, 0.05), 0.4),
         white=mat("F_White", (0.92, 0.92, 0.90), 0.3), jute=mat("F_Jute", (0.72, 0.60, 0.45), 0.95),
         leaf=mat("F_Leaf", (0.20, 0.40, 0.18), 0.8), pot=mat("F_Pot", (0.60, 0.58, 0.55), 0.9))


def box(name, th, x0, y0, z0, x1, y1, z1, m):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 if v.co.x < 0 else x1
        v.co.y = y0 if v.co.y < 0 else y1
        v.co.z = z0 if v.co.z < 0 else z1
    bm.to_mesh(me); bm.free()
    me.materials.append(M[m])
    me["element"], me["th"] = "furniture", th
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)
    return o


def cyl(name, th, cx, cy, z0, z1, r, m, seg=24):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=r, depth=z1 - z0)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(cx, cy, (z0 + z1) / 2))
    bm.to_mesh(me); bm.free()
    me.materials.append(M[m])
    me["element"], me["th"] = "furniture", th
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)


def sphere(name, th, cx, cy, cz, r, m):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r)
    bmesh.ops.translate(bm, verts=bm.verts, vec=(cx, cy, cz))
    bm.to_mesh(me); bm.free()
    me.materials.append(M[m])
    me["element"], me["th"] = "furniture", th
    o = bpy.data.objects.new(name, me)
    col.objects.link(o)


# ---------------- pieces (x0, y0 = min corner; sizes in m) ----------------
def bed(p, x0, y0, w, l, head="-y", f=FL):
    """head against the wall on the -y side (head='-y') or +y side"""
    y_h0, y_h1 = (y0, y0 + 0.08) if head == "-y" else (y0 + l - 0.08, y0 + l)
    box(p + "_Frame", "เตียง (โครงไม้)", x0, y0, f, x0 + w, y0 + l, f + 0.30, "wood_l")
    box(p + "_Mattress", "ที่นอน", x0 + 0.03, y0 + 0.03, f + 0.30, x0 + w - 0.03, y0 + l - 0.03, f + 0.52, "fabric")
    box(p + "_Head", "หัวเตียงบุผ้า", x0 - 0.05, y_h0, f, x0 + w + 0.05, y_h1, f + 1.10, "taupe")
    ty0, ty1 = (y0 + l * 0.55, y0 + l * 0.8) if head == "-y" else (y0 + l * 0.2, y0 + l * 0.45)
    box(p + "_Throw", "ผ้าคลุมเตียง", x0 + 0.02, ty0, f + 0.52, x0 + w - 0.02, ty1, f + 0.55, "sage")
    py0, py1 = (y0 + 0.12, y0 + 0.45) if head == "-y" else (y0 + l - 0.45, y0 + l - 0.12)
    for i, xx in enumerate((x0 + 0.1, x0 + w / 2 + 0.05)):
        box(f"{p}_Pillow{i}", "หมอน", xx, py0, f + 0.52, xx + w / 2 - 0.15, py1, f + 0.66, "white")


def nightstand(p, x0, y0, f=FL):
    box(p, "โต๊ะข้างเตียง", x0, y0, f, x0 + 0.45, y0 + 0.40, f + 0.50, "wood")
    cyl(p + "_Lamp", "โคมตั้งโต๊ะ", x0 + 0.22, y0 + 0.2, f + 0.50, f + 0.85, 0.12, "fabric")


def wardrobe(p, x0, y0, x1, y1, f=FL):
    box(p, "ตู้เสื้อผ้าบานเรียบสีครีม", x0, y0, f, x1, y1, f + 2.40, "fabric")


def sofa_straight(p, x0, y0, w, d, back="+x", f=FL):
    """sofa along y (w = length along y), back on +x or -x side"""
    box(p + "_Base", "โซฟาผ้าครีม", x0, y0, f, x0 + d, y0 + w, f + 0.42, "fabric")
    bx0, bx1 = (x0 + d - 0.20, x0 + d) if back == "+x" else (x0, x0 + 0.20)
    box(p + "_Back", "พนักพิงโซฟา", bx0, y0, f + 0.42, bx1, y0 + w, f + 0.82, "fabric")
    for i, (a0, a1) in enumerate(((y0, y0 + 0.18), (y0 + w - 0.18, y0 + w))):
        box(f"{p}_Arm{i}", "ที่วางแขนโซฟา", x0, a0, f + 0.42, x0 + d, a1, f + 0.62, "fabric")


def plant(p, cx, cy, h=1.4, f=FL):
    cyl(p + "_Pot", "กระถางต้นไม้", cx, cy, f, f + 0.40, 0.20, "terra")
    sphere(p + "_Leaves", "ต้นไม้ใบใหญ่", cx, cy, f + 0.40 + h * 0.45, h * 0.32, "leaf")


def chair(p, x0, y0, f=FL, m="wood_l"):
    box(p + "_Seat", "เก้าอี้", x0, y0, f + 0.42, x0 + 0.45, y0 + 0.45, f + 0.47, m)
    box(p + "_Back", "พนักเก้าอี้", x0, y0, f + 0.47, x0 + 0.45, y0 + 0.05, f + 0.85, m)
    for i, (a, b) in enumerate(((0, 0), (0.41, 0), (0, 0.41), (0.41, 0.41))):
        box(f"{p}_Leg{i}", "ขาเก้าอี้", x0 + a, y0 + b, f, x0 + a + 0.04, y0 + b + 0.04, f + 0.42, "black")


# ---------------- ห้องนอน 1 (x −0.015…4.95, y 4.05…7.515) ----------------
bed("FN_Bed1", 1.40, 4.05, 1.90, 2.10)                     # 6 ft, head on the south wall (AC above)
nightstand("FN_Bed1_NS_L", 0.85, 4.12); nightstand("FN_Bed1_NS_R", 3.40, 4.12)
wardrobe("FN_Bed1_Wardrobe", 4.35, 4.15, 4.95, 6.35)       # east wall, clear of door D3 (y 6.48–7.38)
box("FN_Bed1_Desk", "โต๊ะเครื่องแป้ง", 2.70, 7.05, FL, 3.90, 7.515, FL + 0.75, "wood")
chair("FN_Bed1_Stool", 3.07, 6.55, m="fabric")
box("FN_Bed1_Rug", "พรมสาน", 1.10, 5.60, FL, 3.60, 7.00, FL + 0.01, "jute")
plant("FN_Bed1_Plant", 0.35, 7.15, 1.0)

# ---------------- ห้องนั่งเล่น (x 5.115…9.45, y 0.985…7.515) ----------------
box("FN_Liv_TVStand", "ทีวีสแตนด์ไม้", 5.115, 4.15, FL, 5.515, 5.95, FL + 0.45, "wood")
box("FN_Liv_TV", "ทีวี 55 นิ้ว", 5.13, 4.45, FL + 0.95, 5.18, 5.68, FL + 1.65, "black")
box("FN_Liv_WallPanel", "ผนังไม้หลังทีวี", 5.115, 3.95, FL + 0.45, 5.14, 6.15, FL + 2.40, "wood")
sofa_straight("FN_Liv_Sofa", 7.65, 3.85, 2.30, 0.92, back="+x")
box("FN_Liv_Chaise", "โซฟาตัว L (ส่วนขยาย)", 6.85, 3.85, FL, 7.65, 4.75, FL + 0.42, "fabric")
cyl("FN_Liv_CoffeeTable", "โต๊ะกลางไม้ทรงกลม", 6.55, 5.25, FL, FL + 0.40, 0.42, "wood", 32)
box("FN_Liv_Rug", "พรมสานสีเบจ", 5.85, 3.95, FL, 7.95, 6.55, FL + 0.01, "jute")
box("FN_Liv_Armchair", "อาร์มแชร์ไม้หนังคอนยัค", 7.70, 1.30, FL, 8.45, 2.05, FL + 0.80, "leather")
plant("FN_Liv_Plant1", 9.05, 6.95, 1.6); plant("FN_Liv_Plant2", 9.10, 1.35, 1.4)

# ---------------- ห้องนอน 2 (x 9.55…13.015, y 4.55…7.515) ----------------
bed("FN_Bed2", 11.00, 4.55, 1.60, 2.00)                    # 5 ft, head on the south wall
nightstand("FN_Bed2_NS_L", 10.50, 4.62); nightstand("FN_Bed2_NS_R", 12.55, 4.62)
wardrobe("FN_Bed2_Wardrobe", 9.55, 5.80, 10.15, 7.45)      # west wall, clear of door (y 4.75–5.65)
box("FN_Bed2_Rug", "พรมสาน", 10.60, 6.15, FL, 13.00, 7.30, FL + 0.01, "jute")

# ---------------- ห้องนอน 3 (x 9.55…13.015, y −0.015…2.95) ----------------
bed("FN_Bed3", 11.00, 0.95, 1.60, 2.00, head="+y")         # head on the north wall (AC above)
nightstand("FN_Bed3_NS_L", 10.50, 2.48); nightstand("FN_Bed3_NS_R", 12.55, 2.48)
wardrobe("FN_Bed3_Wardrobe", 9.55, 0.05, 10.15, 1.85)      # west wall, clear of door (y 1.98–2.88)
box("FN_Bed3_Desk", "โต๊ะทำงาน", 11.85, 0.00, FL, 12.95, 0.55, FL + 0.75, "wood_l")

# ---------------- ห้องแต่งตัว / ห้องเก็บของ ----------------
wardrobe("FN_Dress_Wardrobe", -0.015, 0.10, 0.585, 2.35)
box("FN_Dress_Bench", "ม้านั่งบุผ้า", 1.20, 1.10, FL, 2.20, 1.50, FL + 0.45, "taupe")
box("FN_Store_Shelf", "ชั้นวางของ", 4.50, 0.10, FL, 4.95, 3.00, FL + 2.00, "wood_l")

# ---------------- ครัว / ทานข้าว (ใต้หลังคาเพิง, หลังบ้าน) ----------------
box("FN_Kit_CounterW", "เคาน์เตอร์ครัวตู้ล่าง (ซิงก์)", 3.48, 9.30, FL, 4.08, 12.10, FL + 0.86, "wood")
box("FN_Kit_CounterN", "เคาน์เตอร์ครัวตู้ล่าง", 4.08, 11.50, FL, 6.00, 12.10, FL + 0.86, "wood")
box("FN_Kit_TopW", "ท็อปหินสีขาว", 3.46, 9.28, FL + 0.86, 4.10, 12.12, FL + 0.90, "white")
box("FN_Kit_TopN", "ท็อปหินสีขาว", 4.08, 11.48, FL + 0.86, 6.00, 12.12, FL + 0.90, "white")
box("FN_Kit_Upper", "ตู้แขวนไม้ + ชั้นเปิด", 4.08, 11.80, FL + 1.50, 6.00, 12.15, FL + 2.25, "wood_l")
box("FN_Kit_Fridge", "ตู้เย็น", 6.05, 11.45, FL, 6.75, 12.10, FL + 1.80, "white")
box("FN_Kit_Table", "โต๊ะอาหารไม้ 4 ที่", 6.30, 9.90, FL + 0.72, 7.70, 10.70, FL + 0.76, "wood")
for i, (lx, ly) in enumerate(((6.35, 9.95), (7.60, 9.95), (6.35, 10.60), (7.60, 10.60))):
    box(f"FN_Kit_TableLeg{i}", "ขาโต๊ะ", lx, ly, FL, lx + 0.05, ly + 0.05, FL + 0.72, "black")
for i, (cx, cy) in enumerate(((6.50, 9.35), (7.10, 9.35), (6.50, 10.85), (7.10, 10.85))):
    chair(f"FN_Kit_Chair{i}", cx, cy)
for i, cx in enumerate((6.70, 7.30)):
    sphere(f"FN_Kit_Pendant{i}", "โคมหวาย", cx, 10.30, FL + 1.75, 0.18, "jute")

# ---------------- ระเบียงหน้า / หลัง ----------------
box("FN_VerF_Bench", "โซฟาไม้เบาะครีม (ระเบียงหน้า)", 7.30, 0.15, FL - 0.10, 8.90, 0.75, FL + 0.32, "wood_l")
box("FN_VerF_Cushion", "เบาะผ้าครีม", 7.32, 0.17, FL + 0.32, 8.88, 0.73, FL + 0.42, "fabric")
plant("FN_VerF_Plant", 9.20, 0.45, 1.2, FL - 0.10)
cyl("FN_VerR_Table", "โต๊ะกลมระเบียงหลัง", 4.70, 8.35, FL - 0.10, FL + 0.45, 0.30, "wood", 24)
chair("FN_VerR_Chair0", 3.80, 8.10, FL - 0.10); chair("FN_VerR_Chair1", 5.15, 8.10, FL - 0.10)
plant("FN_VerR_Plant", 3.70, 8.80, 1.0, FL - 0.10)

# ---------------- ห้องน้ำ: ของแต่งเล็กน้อย (สุขภัณฑ์มีแล้วใน ST16) ----------------
cyl("FN_Bath1_Mat", "พรมเชือกกลม", 1.90, 3.15, 0.70, 0.71, 0.30, "jute")
cyl("FN_Bath2_Mat", "พรมเชือกกลม", 11.40, 3.80, 0.70, 0.71, 0.30, "jute")

n = len(col.objects)
bpy.ops.wm.save_mainfile()
print("FURNITURE DONE", n, "objects in", C_FURN)
