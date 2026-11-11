# Web Rotor (เว็บโรเตอร์) สำหรับ NVDA

ส่วนเสริมนี้เพิ่มเมนูหมุน (Rotor) แบบเดียวกับ VoiceOver ให้ NVDA ใช้สำรวจองค์ประกอบของหน้าเว็บได้อย่างรวดเร็ว
รองรับ 23 หมวด เช่น หัวเรื่อง ลิงก์ จุดสังเกต ปุ่ม ช่องแบบฟอร์ม และตาราง แต่ละหมวดเป็นแท็บ พิมพ์ตัวอักษรเพื่อกระโดดไปยังรายการ
คีย์ลัด Alt+ตัวอักษรใช้ได้ทั้งแป้นอังกฤษและไทย และแสดงผลได้ 2 ภาษา (ไทย/อังกฤษ)

- เวอร์ชันปัจจุบัน: 1.8.2
- รองรับ NVDA 2023.2 ขึ้นไป (ทดสอบล่าสุดกับ 2026.3)
- ผู้พัฒนา: Peera Pilarit

## ปุ่มลัดหลัก

| ปุ่ม | หน้าที่ |
|---|---|
| Control+Windows+U | เปิดเว็บโรเตอร์ (ต้องอยู่ในโหมดเรียกดู) |
| Control+Windows+Shift+U | เปิดหน้าตั้งค่า |
| NVDA+F7 | เปิดเว็บโรเตอร์แทน Elements List (เมื่อเปิดตัวเลือกนี้ในหน้าตั้งค่า) |

คู่มือฉบับเต็มอยู่ที่ [addon/doc/th/readme.md](addon/doc/th/readme.md)

## สร้างไฟล์ติดตั้ง

```
python build.py
```

ได้ไฟล์ `dist/webRotor-<เวอร์ชัน>.nvda-addon` จากนั้นเปิดไฟล์นี้ใน Windows เพื่อติดตั้งใน NVDA

## ออกเวอร์ชันใหม่และส่งขึ้น NVDA Add-on Store

1. แก้ `version` และ `changelog` ใน `addon/manifest.ini` และ `addon/locale/th/manifest.ini` แล้ว merge เข้า `main`
2. เมื่อ merge เข้า `main` แล้ว GitHub Actions จะ build และสร้าง Release (tag เช่น `v1.8.0`) พร้อมไฟล์ `.nvda-addon` ให้อัตโนมัติ ถ้าเวอร์ชันนั้นยังไม่เคยออก
3. ส่งลิงก์ไฟล์ใน Release ผ่านฟอร์ม "Add-on registration" ที่ [nvaccess/addon-datastore](https://github.com/nvaccess/addon-datastore/issues/new/choose)

## English

Web Rotor adds a VoiceOver-style rotor to NVDA for exploring web page elements by category.
See the [English user guide](addon/doc/en/readme.md). Licensed under the GNU GPL v2 ([LICENSE.md](LICENSE.md)).
