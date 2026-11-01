# Web Rotor — คู่มือโปรเจกต์สำหรับ Claude

ส่วนเสริม (add-on) ของโปรแกรมอ่านหน้าจอ NVDA ที่เพิ่มเมนูหมุน (Rotor) แบบ VoiceOver
สำหรับสำรวจองค์ประกอบของหน้าเว็บในโหมดเรียกดู (Browse Mode) ผู้ใช้หลักคือคนตาบอดชาวไทย
ผู้พัฒนา: Peera Pilarit — ตอบและเขียนคอมเมนต์เป็นภาษาไทย

## โครงสร้าง

```
addon/                       # ทุกอย่างในนี้จะถูกบีบอัดเป็น .nvda-addon
  manifest.ini               # name, version, minimumNVDAVersion (2023.2), lastTestedNVDAVersion
  globalPlugins/webRotor/
    __init__.py              # GlobalPlugin: ปุ่มลัด, เมนู Preferences, เปิดหน้าต่าง
    rotorDialog.py           # หน้าต่างโรเตอร์ (ช่องกรอง, รายการ, เปลี่ยนหมวด, Alt+ตัวอักษร)
    settingsDialog.py        # หน้าตั้งค่า (ภาษา, เลือก/จัดลำดับหมวด, ตัวเลือกต่างๆ)
    categories.py            # MASTER_ORDER 23 หมวด, DEFAULT_ENABLED, config section "webRotor"
    strings.py               # ข้อความ 2 ภาษา (en/th) ผ่าน tr(key); ค่าเริ่มต้นภาษาอังกฤษ
  doc/th/readme.md           # คู่มือผู้ใช้ภาษาไทย
build.py                     # python build.py → dist/webRotor-<version>.nvda-addon
```

## ปุ่มลัด

- `Control+Windows+U` เปิดเว็บโรเตอร์
- `Control+Windows+Shift+U` เปิดหน้าตั้งค่า (มีในเมนู Preferences ด้วย)
- `NVDA+F7` เปิดเว็บโรเตอร์แทน Elements List เฉพาะเมื่อเปิดตัวเลือก `overrideElementsList`
  ถ้าไม่เปิด ต้องเรียก Elements List เดิมของ NVDA ตามปกติ

## กฎสำคัญ (ห้ามละเมิด)

1. **`gui.mainFrame.prePopup()` และ `postPopup()` ต้องเรียกเป็นคู่เสมอ** ทุกเส้นทางที่ปิดหน้าต่าง
   (Esc, Enter, ปิดหน้าต่าง, เกิด exception) ต้องเรียก `postPopup()` ครั้งเดียวพอดี
   การเรียกไม่สมดุลเคยทำให้ NVDA ค้างทั้งระบบ (แก้ไปแล้วในรอบพัฒนาก่อนหน้า)
2. งาน GUI ทั้งหมดต้องรันบน main thread ผ่าน `wx.CallAfter`
3. ข้อความที่ผู้ใช้ได้ยินหรือเห็นต้องอยู่ใน `strings.py` และมีครบทั้ง `en` และ `th` ห้ามเขียนข้อความลงในโค้ดตรงๆ
4. ห้ามเปลี่ยนพฤติกรรมเดิมของ NVDA โดยผู้ใช้ไม่ได้เลือกเอง ฟีเจอร์ที่เสี่ยง (เช่น `blockOtherGestures`) ต้องปิดเป็นค่าเริ่มต้น
5. ทุกการเปลี่ยนแปลงต้องใช้งานได้ด้วยคีย์บอร์ดล้วนและมีเสียงตอบรับที่ชัดเจน (ui.message)
6. เพิ่มคีย์ใน config ผ่าน `categories.registerConfig()` เท่านั้น และต้องมีค่า default

## การออกเวอร์ชัน

1. แก้ `version` ใน `addon/manifest.ini` และบรรทัดเวอร์ชันใน `addon/doc/th/readme.md`
2. อัปเดต `lastTestedNVDAVersion` ถ้าทดสอบกับ NVDA รุ่นใหม่
3. `python build.py` แล้วทดสอบติดตั้งบน Windows จริงก่อนแจก

## การทำงานร่วมกัน

- ทำงานบน branch แยก แล้วเปิด Pull Request ให้ Peera รีวิวก่อน merge เข้า `main`
- ทดสอบใน Linux ทำได้แค่ตรวจไวยากรณ์ (`python -m py_compile`) ส่วนการทดสอบจริงต้องทำใน NVDA บน Windows
