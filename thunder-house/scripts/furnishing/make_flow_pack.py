# -*- coding: utf-8 -*-
"""Build flow_pack/<id>/ for Google Flow: 1_render.png, 2_idmap.png, prompt_image.txt, prompt_video.txt (KK01 style)."""
import os, shutil
H = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(H, "renders")
STYLE = ("warm contemporary with modern tropical touches: warm white lime-plaster walls, mid-tone oak and walnut wood, "
         "cream linen and boucle fabric, woven jute, terracotta and sage-green accents, matte black metal details, "
         "large leafy plants in terracotta pots, earth-tone abstract art, rattan pendant lamps")
LEG_IN = ("red = warm white lime-plaster walls; yellow = large light beige porcelain floor tiles; "
          "purple = the open roof void above the walls: replace it with a flat white gypsum ceiling with a warm hidden LED cove; "
          "dark blue = black aluminium window frames and white doors; blue = window glass with soft daylight; "
          "green = warm oak and walnut wood; light green = cream linen / boucle fabric, bedding and woven rugs; "
          "grey = matte black metal; lime green = leafy plants; orange = terracotta pots")
ROOMS = {
    "01_exterior": dict(what="single-storey Thai house, front view from the garden", ext=True,
                        keep="the house shape, the dark grey hip roof and its colour, every column, arched window, window and door (front door open), the steps and the porch",
                        place="the bench by the door = a wooden outdoor sofa with cream cushions; the green balls = potted olive trees",
                        add="a stepping-stone path from the camera to the steps, lawn, tropical shrubs along the walls, a few tree branches framing the top corners, warm porch lights",
                        light="golden hour, clear sky with light clouds", move="slow steady dolly forward along the path toward the open front door; foreground branches sway in the breeze"),
    "02_living": dict(what="living room, view from the TV wall toward the L-shaped sofa",
                      keep="the L-shaped sofa, the round coffee table in the foreground, the plant, every door and window",
                      place="the block sofa = a low cream boucle L-shaped sofa with linen cushions; the round block = a solid walnut round coffee table; the green ball = a large fiddle-leaf fig in a terracotta pot",
                      add="a light woven jute rug, ceramic vase and books on the table, framed earth-tone abstract art on the plain wall, a rattan floor lamp",
                      light="soft afternoon daylight", move="slow dolly-in over the coffee table toward the sofa, symmetric framing kept centred"),
    "03_kitchen": dict(what="kitchen and dining, view across the dining table toward the counter and window",
                       keep="the L-shaped counter, the tall fridge, the dining table with four chairs, the two pendant lamps, the window",
                       place="the counter blocks = walnut base cabinets with a white stone worktop and white tile splashback, lit open wood shelves; the white tall box = a built-in white fridge; the balls = two rattan pendant lamps; the table = a solid oak dining table with cream upholstered chairs",
                       add="fresh herbs and a fruit bowl, ceramic jars on the shelves, a woven runner on the table",
                       light="soft morning daylight", move="slow lateral slide along the counter toward the window, table in the foreground for parallax"),
    "04_bed1": dict(what="master bedroom, front view of the bed", keep="the bed, its headboard, both bedside tables and lamps, every window and door",
                    place="the bed block = a low oak bed with a cream upholstered headboard against vertical wood slats with a hidden warm light; the cylinders = linen bedside lamps",
                    add="layered linen bedding in beige and olive, a knit throw, a jute rug, a plant in an empty corner, framed abstract art above the headboard",
                    light="soft afternoon daylight", move="slow dolly-in toward the headboard; sheer curtain moves gently"),
    "05_bed2": dict(what="bedroom 2, front view of the bed", keep="the bed, its headboard, both bedside tables and lamps, the wardrobe, every window and door",
                    place="the bed block = a low walnut bed with a taupe upholstered headboard; the cylinders = ceramic bedside lamps",
                    add="layered cream and sage bedding, a woven rug, sheer linen curtains on the window, a small plant",
                    light="soft daylight", move="slow arc around the foot of the bed toward the headboard"),
    "06_bed3": dict(what="bedroom 3, front view of the bed", keep="the bed, its headboard, both bedside tables and lamps, the desk, every window and door",
                    place="the bed block = a light oak bed with a cream headboard; the cylinders = rattan bedside lamps",
                    add="cream and terracotta bedding, a jute rug, a reading corner plant",
                    light="soft daylight", move="slow dolly-in toward the headboard; daylight shifts subtly"),
}
END = "Photorealistic real-estate interior film, no people, no text."
os.makedirs(os.path.join(H, "flow_pack"), exist_ok=True)
for rid, r in ROOMS.items():
    d = os.path.join(H, "flow_pack", rid)
    os.makedirs(d, exist_ok=True)
    shutil.copy(os.path.join(R, rid + ".png"), os.path.join(d, "1_render.png"))
    shutil.copy(os.path.join(R, rid + "_idmap.png"), os.path.join(d, "2_idmap.png"))
    leg = LEG_IN if not r.get("ext") else ("red = white plaster walls; purple = dark grey concrete roof tiles; dark blue = black aluminium frames; "
                                           "blue = window glass; green = warm wood door and bench; orange = light concrete plinth, steps and paving; "
                                           "olive = lawn; lime green = plants")
    p = (f"Image 1 is a 3D render of a real house: {r['what']}.\n"
         f"Image 2 is its Material ID map: the same camera, every surface painted one flat colour that tells you its material.\n"
         f"Colour legend: {leg}.\n"
         f"Create a photorealistic, magazine-quality {'architectural' if r.get('ext') else 'interior'} photograph of the exact scene in Image 1, styled in {STYLE}. "
         f"Use Image 2 to place each material exactly where its colour is; do not show any colour from Image 2 in the result.\n"
         f"KEEP EXACTLY: the camera position, angle and framing (do not zoom, do not rotate, do not recompose), every wall, {r['keep']}.\n"
         f"Objects that are simple blocky placeholders become realistic high-end versions at exactly the same position and size: {r['place']}.\n"
         f"ADD styling only in empty space, never blocking a window or door: {r['add']}.\n"
         f"Realism: {r['light']} with gentle shadows, warm bounce light, real material textures, light depth of field, full-frame camera, vertical lines perfectly straight. No people, no text, no watermark.\n")
    v = (f"{r['move']}. Eye level on a steady gimbal, no camera shake. The room stays exactly the same: no objects appear, disappear, move or change shape. {END}\n")
    open(os.path.join(d, "prompt_image.txt"), "w", encoding="utf-8").write(p)
    open(os.path.join(d, "prompt_video.txt"), "w", encoding="utf-8").write(v)
    print("pack", rid)
open(os.path.join(H, "flow_pack", "README.txt"), "w", encoding="utf-8").write(
    "วิธีใช้กับ Google Flow (ทำทีละห้อง)\n"
    "1. เปิด https://labs.google/flow → New project\n"
    "2. Image: เลือก Nano Banana Pro (ถ้าโควตาหมดใช้ Nano Banana 2.1) · แนวตั้ง 9:16\n"
    "   ใส่รูปตามลำดับ 1_render.png แล้ว 2_idmap.png · วางข้อความจาก prompt_image.txt · กด Generate\n"
    "3. เลือกรูปที่ดีที่สุด บันทึกชื่อ <ห้อง>_real.png ไว้ในโฟลเดอร์ของห้องนั้น (ลอง 2–3 ครั้งต่อห้องเป็นเรื่องปกติ)\n"
    "4. บอก Claude ว่า \"ตรวจรูป\" → Claude ซ้อนเส้นจาก Blender ตรวจว่าผนัง ประตู หน้าต่างอยู่ที่เดิม\n"
    "5. (ไม่บังคับ) Video: Frames to Video · start frame = <ห้อง>_real.png · 9:16 · Omni Flash 1.2 · 5 s · 720p\n"
    "   วางข้อความจาก prompt_video.txt · ดูเครดิตบนปุ่ม Generate ก่อนกด · บันทึกเป็น <ห้อง>.mp4\n"
    "ภาพที่ได้เป็นภาพจาก AI — ระบุทุกครั้งเมื่อนำไปใช้ขาย\n")
