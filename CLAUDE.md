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
    rotorDialog.py           # หน้าต่างโรเตอร์ (แท็บต่อหมวด, รายการ, พิมพ์กระโดด, Alt+ตัวอักษรไทย/อังกฤษ)
    settingsDialog.py        # หน้าตั้งค่า (ภาษา, เลือก/จัดลำดับหมวด, ตัวเลือกต่างๆ)
    categories.py            # MASTER_ORDER 23 หมวด, DEFAULT_ENABLED, config section "webRotor"
    strings.py               # ข้อความ 2 ภาษา (en/th) ผ่าน tr(key); ค่าเริ่มต้นภาษาอังกฤษ
  locale/th/manifest.ini     # summary/description/changelog ภาษาไทย (manifest หลักเป็นภาษาอังกฤษ)
  doc/th/readme.md           # คู่มือผู้ใช้ภาษาไทย
  doc/en/readme.md           # คู่มือผู้ใช้ภาษาอังกฤษ (build แปลงเป็น readme.html ให้ปุ่ม Help ของ NVDA)
build.py                     # python build.py → dist/webRotor-<version>.nvda-addon (ต้อง pip install markdown)
.github/workflows/release.yml  # merge เข้า main ที่มีเวอร์ชันใหม่ → build และสร้าง GitHub Release อัตโนมัติ
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
7. **ห้ามให้ `decide_executeGesture` คืน False กับทุกปุ่ม** NVDA จะกลืนปุ่มที่ถูกบล็อกทิ้ง หน้าต่างจะไม่ได้รับ
   ลูกศร/Enter/Esc เลย และ NVDA จะเงียบ (เคยเกิดในโรเตอร์และหน้าตั้งค่า แก้ใน 1.8.1) ปุ่มที่ไม่ได้ผูกคำสั่ง
   และปุ่มที่หน้าต่างใช้ต้องปล่อยผ่านเสมอ ห้ามเรียก wx ใน decider และถ้าเกิด exception ต้องปล่อยผ่าน
8. รายการที่มีช่องติ๊ก ใช้ `gui.nvdaControls.CustomCheckListBox` ไม่ใช้ `wx.CheckListBox` ตรงๆ
   เพราะ NVDA อ่านสถานะเลือก/ไม่เลือกของ `wx.CheckListBox` ไม่ได้

## การออกเวอร์ชัน

1. แก้ `version` และ `changelog` ใน `addon/manifest.ini` และ `changelog` ใน `addon/locale/th/manifest.ini`
   รวมถึงบรรทัดเวอร์ชันใน `addon/doc/th/readme.md` และ `addon/doc/en/readme.md`
2. อัปเดต `lastTestedNVDAVersion` ถ้าทดสอบกับ NVDA รุ่นใหม่
3. `python build.py` แล้วทดสอบติดตั้งบน Windows จริงก่อนแจก
4. merge เข้า `main` แล้ว workflow จะสร้าง tag `vX.Y.Z` และ Release ให้เอง ถ้าเวอร์ชันนั้นยังไม่มี Release
   (session ของ Claude สร้าง tag/Release ตรงๆ ไม่ได้ จึงใช้วิธีนี้)
5. ส่งขึ้น NVDA Add-on Store ผ่านฟอร์ม "Add-on registration" ที่ nvaccess/addon-datastore
   (Download URL = ลิงก์ไฟล์ .nvda-addon ใน Release, Source URL = ลิงก์ repo, License = GPL v2, Channel = stable)
6. เปลี่ยนคำอธิบายหรือฟีเจอร์ ต้องแก้ทั้ง manifest อังกฤษและไทย และคู่มือทั้งสองภาษา

## การทำงานร่วมกัน

- ทำงานบน branch แยก แล้วเปิด Pull Request ให้ Peera รีวิวก่อน merge เข้า `main`
- ทดสอบใน Linux ทำได้แค่ตรวจไวยากรณ์ (`python -m py_compile`) ส่วนการทดสอบจริงต้องทำใน NVDA บน Windows
