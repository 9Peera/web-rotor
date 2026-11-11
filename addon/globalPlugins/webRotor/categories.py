# -*- coding: utf-8 -*-
# Web Rotor add-on for NVDA
# รายการหมวดหมู่ทั้งหมดที่รองรับ + การจัดการค่าตั้งค่า (เปิด/ปิด, ลำดับ, ภาษา, การแทนที่ NVDA+F7)

import config

from . import strings

# รายการ itemType ทั้งหมดที่รองรับ ตามลำดับมาตรฐาน (อ้างอิงจากชุด itemType ที่ใช้ได้จริงกับ
# BrowseModeTreeInterceptor._iterNodesByType ของ NVDA - ชุดเดียวกับปุ่มลัดนำทางตัวอักษรเดี่ยวของโหมดเรียกดู)
MASTER_ORDER = [
	"heading",
	"link",
	"visitedLink",
	"unvisitedLink",
	"landmark",
	"mainLandmark",
	"button",
	"formField",
	"edit",
	"checkBox",
	"radioButton",
	"comboBox",
	"table",
	"list",
	"listItem",
	"graphic",
	"blockQuote",
	"frame",
	"separator",
	"embeddedObject",
	"annotation",
	"paragraph",
	"article",
]

# หมวดหมู่ที่เปิดใช้งานเป็นค่าเริ่มต้น (เหมือนชุดเดิมของเวอร์ชันแรก เพื่อไม่ให้พฤติกรรมเปลี่ยนไปโดยไม่ตั้งใจ)
DEFAULT_ENABLED = [
	"heading",
	"link",
	"landmark",
	"button",
	"formField",
	"table",
	"list",
]

CONFIG_SECTION = "webRotor"


def registerConfig():
	"""ลงทะเบียนโครงสร้างค่าตั้งค่าของส่วนเสริมนี้กับ config ของ NVDA
	ต้องเรียกครั้งเดียวตอน GlobalPlugin เริ่มทำงาน ก่อนมีการอ่าน/เขียนค่าใดๆ
	"""
	confspec = {
		"categories": "string(default='%s')" % ",".join(DEFAULT_ENABLED),
		# ถ้าเป็นจริง: กด NVDA+F7 จะเปิดเว็บโรเตอร์แทนกล่องโต้ตอบ Elements List มาตรฐานของ NVDA
		"overrideElementsList": "boolean(default=false)",
		# ถ้าเป็นจริง: ปุ่มลัด/คำสั่งอื่นๆ ของ NVDA จะถูกปิดใช้งานชั่วคราวขณะเว็บโรเตอร์เปิดอยู่
		# ค่าเริ่มต้นเป็นเท็จ (ปิด) เนื่องจากอาจชนกับส่วนเสริมอื่นบางตัวจนทำให้ NVDA ค้างได้ในบางเครื่อง
		"blockOtherGestures": "boolean(default=false)",
		# ชุดปุ่มลัดที่ชนกับส่วนเสริมอื่นที่เคยแจ้งผู้ใช้แล้ว (จะแจ้งตอนเปิด NVDA เฉพาะเมื่อชุดนี้เปลี่ยน)
		"notifiedConflicts": "string(default='')",
	}
	strings.registerConfigKey(confspec)  # เพิ่มคีย์ "language" (ค่าเริ่มต้น = อังกฤษ)
	config.conf.spec[CONFIG_SECTION] = confspec


def getEnabledCategories():
	"""คืนรายชื่อ itemType ที่ผู้ใช้เปิดใช้งาน เรียงตามลำดับการหมุนที่ผู้ใช้ตั้งค่าไว้"""
	raw = config.conf[CONFIG_SECTION]["categories"]
	items = [s.strip() for s in raw.split(",") if s.strip()]
	# กรองรายการที่ไม่รู้จักออก (เผื่อกรณีอัปเดตส่วนเสริมแล้วบางหมวดถูกเปลี่ยนชื่อ/ลบไป)
	items = [i for i in items if i in MASTER_ORDER]
	if not items:
		items = list(DEFAULT_ENABLED)
	return items


def setEnabledCategories(itemTypes):
	"""บันทึกรายชื่อ itemType ที่เปิดใช้งาน (ตามลำดับที่ต้องการ) ลง config"""
	config.conf[CONFIG_SECTION]["categories"] = ",".join(itemTypes)


def getLabel(itemType):
	"""คืนป้ายชื่อของหมวดหมู่ตามภาษาที่ตั้งค่าไว้ปัจจุบัน"""
	lang = strings.getLang()
	table = strings.CATEGORY_LABELS.get(lang, strings.CATEGORY_LABELS[strings.DEFAULT_LANG])
	return table.get(itemType, strings.CATEGORY_LABELS[strings.DEFAULT_LANG].get(itemType, itemType))


def getOverrideElementsList():
	"""คืนค่า True ถ้าผู้ใช้เลือกให้ NVDA+F7 เปิดเว็บโรเตอร์แทน Elements List เดิม"""
	return bool(config.conf[CONFIG_SECTION]["overrideElementsList"])


def setOverrideElementsList(value):
	config.conf[CONFIG_SECTION]["overrideElementsList"] = bool(value)


def getBlockOtherGestures():
	"""คืนค่า True ถ้าผู้ใช้เปิดใช้งานการบล็อกปุ่มลัดอื่นของ NVDA ขณะเว็บโรเตอร์เปิดอยู่ (ค่าเริ่มต้น: ปิด)"""
	return bool(config.conf[CONFIG_SECTION]["blockOtherGestures"])


def setBlockOtherGestures(value):
	config.conf[CONFIG_SECTION]["blockOtherGestures"] = bool(value)


def getNotifiedConflicts():
	return str(config.conf[CONFIG_SECTION]["notifiedConflicts"] or "")


def setNotifiedConflicts(value):
	config.conf[CONFIG_SECTION]["notifiedConflicts"] = str(value or "")
