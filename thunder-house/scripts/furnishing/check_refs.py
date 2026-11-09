# -*- coding: utf-8 -*-
"""ตรวจว่ารูปอ้างอิงเฟอร์นิเจอร์ครบหรือยัง:  python check_refs.py
ใส่รูป (.jpg .jpeg .png .webp) ลงโฟลเดอร์ใน refs/ ตามห้อง แล้วรันสคริปต์นี้ (หรือบอก Claude ว่า "เช็กรูป")"""
import os, sys
H = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(H, "refs")
EXT = (".jpg", ".jpeg", ".png", ".webp")
# โฟลเดอร์ : (ชื่อ, ขั้นต่ำ, บังคับไหม, ควรมีอะไร)
NEED = [
    ("00_style",   "ภาพสไตล์รวมทั้งบ้าน (mood board)", 3, True,  "โทนสี วัสดุ แสงที่ชอบ"),
    ("01_living",  "ห้องนั่งเล่น",                     2, True,  "ภาพห้อง + โซฟา โต๊ะกลาง ทีวีสแตนด์"),
    ("02_bedroom", "ห้องนอน (ใช้กับห้องนอน 1–3)",       2, True,  "ภาพห้อง + เตียง ตู้เสื้อผ้า"),
    ("03_kitchen", "ครัว / ทานข้าว",                    2, True,  "ภาพห้อง + เคาน์เตอร์ โต๊ะอาหาร"),
    ("04_bath",    "ห้องน้ำ",                           1, True,  "ภาพห้องน้ำโทนที่ชอบ"),
    ("05_verandah", "ระเบียงหน้า / หลัง",               1, False, "ชุดนั่งเล่น ต้นไม้ (ไม่บังคับ)"),
    ("06_furniture", "เฟอร์นิเจอร์รายชิ้น",            0, False, "ภาพชิ้นที่อยากได้เป๊ะ ๆ ตั้งชื่อไฟล์ตามชิ้น เช่น sofa_1.jpg (ไม่บังคับ)"),
]


def main():
    ok_all = True
    print(f"{'โฟลเดอร์':<14}{'มี':>4}{'ขั้นต่ำ':>8}  สถานะ")
    for d, name, mn, must, hint in NEED:
        p = os.path.join(REFS, d)
        n = len([f for f in os.listdir(p) if f.lower().endswith(EXT)]) if os.path.isdir(p) else 0
        if n >= mn:
            st = "✅ ครบ"
        elif must:
            st = f"❌ ขาด {mn - n} รูป — {hint}"; ok_all = False
        else:
            st = f"⚪ ไม่บังคับ — {hint}"
        print(f"{d:<14}{n:>4}{mn:>8}  {name}: {st}")
    sty = os.path.join(H, "style.txt")
    has_txt = os.path.exists(sty) and open(sty, encoding="utf-8").read().strip() and "เขียนสไตล์" not in open(sty, encoding="utf-8").read()
    print("style.txt:", "✅ มีคำบอกสไตล์" if has_txt else "⚪ ยังไม่เขียน (ไม่บังคับ — Claude เขียนให้จากรูปได้)")
    print("\nผล:", "ครบแล้ว → ไปขั้นที่ 2 (Claude เขียน prompt สไตล์จากรูป)" if ok_all else "ยังไม่ครบ")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
