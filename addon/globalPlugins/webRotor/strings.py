# -*- coding: utf-8 -*-
# Web Rotor add-on for NVDA
# ศูนย์รวมคำแปลของ UI ทั้งหมด (ไทย/อังกฤษ) และการตั้งค่าภาษาที่ใช้แสดงผล
# หมายเหตุ: การตั้งค่าภาษานี้เป็นของส่วนเสริม Web Rotor เอง แยกต่างหากจากภาษาที่ใช้แสดงผลของ NVDA เอง

import config

CONFIG_SECTION = "webRotor"
DEFAULT_LANG = "en"
SUPPORTED_LANGS = ("en", "th")


def registerConfigKey(confspec):
	"""เพิ่มคีย์การตั้งค่าภาษาเข้าไปใน confspec ที่ categories.registerConfig() จะนำไปลงทะเบียนต่อ"""
	confspec["language"] = "string(default='%s')" % DEFAULT_LANG


def getLang():
	try:
		lang = config.conf[CONFIG_SECTION]["language"]
	except KeyError:
		# ยังไม่ได้ลงทะเบียน config (เช่น ถูกเรียกก่อน categories.registerConfig())
		return DEFAULT_LANG
	if lang not in SUPPORTED_LANGS:
		lang = DEFAULT_LANG
	return lang


def setLang(lang):
	if lang not in SUPPORTED_LANGS:
		lang = DEFAULT_LANG
	config.conf[CONFIG_SECTION]["language"] = lang


def tr(key, **kwargs):
	"""คืนข้อความตามภาษาที่ตั้งค่าไว้ปัจจุบัน หากไม่พบคีย์ จะใช้ภาษาอังกฤษเป็นค่าสำรอง"""
	lang = getLang()
	table = UI_STRINGS.get(lang, UI_STRINGS[DEFAULT_LANG])
	text = table.get(key)
	if text is None:
		text = UI_STRINGS[DEFAULT_LANG].get(key, key)
	if kwargs:
		try:
			return text.format(**kwargs)
		except (KeyError, IndexError):
			return text
	return text


# ป้ายชื่อของแต่ละหมวดหมู่ (itemType -> ป้ายชื่อที่แสดง) แยกตามภาษา
CATEGORY_LABELS = {
	"en": {
		"heading": "Headings",
		"link": "Links (all)",
		"visitedLink": "Visited links",
		"unvisitedLink": "Unvisited links",
		"landmark": "Landmarks",
		"mainLandmark": "Main landmark",
		"button": "Buttons",
		"formField": "Form fields (all)",
		"edit": "Edit fields",
		"checkBox": "Checkboxes",
		"radioButton": "Radio buttons",
		"comboBox": "Combo boxes",
		"table": "Tables",
		"list": "Lists",
		"listItem": "List items",
		"graphic": "Graphics",
		"blockQuote": "Block quotes",
		"frame": "Frames",
		"separator": "Separators",
		"embeddedObject": "Embedded objects (audio, video, app, etc.)",
		"annotation": "Annotations (comments)",
		"paragraph": "Paragraphs",
		"article": "Articles",
	},
	"th": {
		"heading": "หัวเรื่อง",
		"link": "ลิงก์ (ทั้งหมด)",
		"visitedLink": "ลิงก์ที่เคยเยี่ยมชมแล้ว",
		"unvisitedLink": "ลิงก์ที่ยังไม่ได้เยี่ยมชม",
		"landmark": "จุดสังเกต (Landmark)",
		"mainLandmark": "จุดสังเกตหลัก (Main Landmark)",
		"button": "ปุ่ม",
		"formField": "ช่องแบบฟอร์ม (ทั้งหมด)",
		"edit": "ช่องพิมพ์ข้อความ (Edit field)",
		"checkBox": "กล่องกาเครื่องหมาย (Checkbox)",
		"radioButton": "ปุ่มตัวเลือก (Radio button)",
		"comboBox": "กล่องรายการเลือก (Combo box)",
		"table": "ตาราง",
		"list": "รายการ (List)",
		"listItem": "รายการย่อยในลิสต์ (List item)",
		"graphic": "รูปภาพ/กราฟิก",
		"blockQuote": "ข้อความอ้างอิง (Block quote)",
		"frame": "เฟรม (Frame)",
		"separator": "เส้นแบ่ง (Separator)",
		"embeddedObject": "อ็อบเจกต์ฝังตัว (เสียง/วิดีโอ/แอปพลิเคชัน ฯลฯ)",
		"annotation": "หมายเหตุ/ข้อคิดเห็น (Annotation)",
		"paragraph": "ย่อหน้า",
		"article": "บทความ (Article)",
	},
}

# ตัวอักษรคีย์ลัด (กด Alt+ตัวอักษรนี้ในหน้าต่างเว็บโรเตอร์เพื่อกระโดดตรงไปหมวดหมู่นั้นทันที)
# ทั้งสองชุดใช้ได้พร้อมกันเสมอ ไม่ขึ้นกับภาษาที่ตั้งค่าไว้: แป้นอังกฤษใช้ชุด "en" แป้นไทยใช้ชุด "th"
# ไม่ซ้ำกันเองภายในแต่ละชุด
CATEGORY_SHORTCUTS = {
	"en": {
		"heading": "H", "link": "K", "visitedLink": "V", "unvisitedLink": "U",
		"landmark": "D", "mainLandmark": "M", "button": "B", "formField": "O",
		"edit": "E", "checkBox": "X", "radioButton": "R", "comboBox": "C",
		"table": "T", "list": "L", "listItem": "I", "graphic": "G",
		"blockQuote": "Q", "frame": "N", "separator": "S", "embeddedObject": "J",
		"annotation": "A", "paragraph": "P", "article": "Z",
	},
	"th": {
		"heading": "ห", "link": "ล", "visitedLink": "ข", "unvisitedLink": "ค", "landmark": "จ",
		"mainLandmark": "ง", "button": "ป", "formField": "ช", "edit": "ฉ", "checkBox": "ซ",
		"radioButton": "ญ", "comboBox": "ฎ", "table": "ต", "list": "ร", "listItem": "ฏ",
		"graphic": "ฐ", "blockQuote": "ณ", "frame": "ฟ", "separator": "ด", "embeddedObject": "อ",
		"annotation": "ถ", "paragraph": "ย", "article": "บ",
	},
}

# ข้อความ UI ทั้งหมดของส่วนเสริม แยกตามภาษา
UI_STRINGS = {
	"en": {
		# --- Preferences menu ---
		"prefsMenuItem": "Web Rotor settings...",
		"prefsMenuItemHelp": "Choose and reorder the categories shown in Web Rotor",

		# --- GlobalPlugin messages ---
		"notBrowseMode": "Web Rotor is only available in documents that support browse mode.",
		"inFocusMode": "Please exit focus mode (press NVDA+Space or Escape) and try again.",
		"docOpenWebRotor": "Opens Web Rotor to explore elements of the current web page, such as headings, links, and landmarks",
		"docOpenWebRotorSettings": "Opens Web Rotor settings, to choose and reorder the categories shown",
		"docElementsListOrRotor": "Opens NVDA's standard Elements List, or Web Rotor, depending on the Web Rotor settings",

		# --- Rotor dialog ---
		"rotorTitle": "Web Rotor",
		"rotorHint": (
			"Up/Down arrow: move through the list \u00b7 Type a letter: jump to an item starting with it \u00b7 "
			"Left/Right arrow: change category \u00b7 Shift+Tab: category tabs \u00b7 "
			"Alt+letter (English or Thai): jump to a category \u00b7 Enter: go to this position \u00b7 Esc: close"
		),
		"rotorHintBlockNotice": " \u00b7 (other NVDA commands are temporarily disabled while this window is open)",
		"noCategoriesSelected": "No categories have been selected in Web Rotor settings.",
		"noLabel": "(no label)",
		"categoryLabelPlain": "{category} \u2014 {total} item(s)",
		"categoryLabelEmpty": "{category} \u2014 no items on this page",
		"moveToFailed": "Could not go to this position. The page may have changed.",

		# --- Settings dialog ---
		"settingsTitle": "Web Rotor settings",
		"settingsInstructions": (
			"Check the categories you want to appear in Web Rotor (Control+Windows+U).\n"
			"Use the \u201cMove up / Move down\u201d buttons to set the order used when rotating with Left/Right arrow."
		),
		"categoriesListLabel": "Categories (&C):",
		"moveUpBtn": "Move &up",
		"moveDownBtn": "Move &down",
		"restoreDefaultsBtn": "&Restore defaults",
		"restoredDefaults": "Defaults restored",
		"languageLabel": "Language used by Web Rotor (&L):",
		"languageEnglish": "English",
		"languageThai": "Thai (\u0e44\u0e17\u0e22)",
		"overrideElementsListCheckbox": "Use NVDA+F7 to open Web Rotor instead of NVDA's standard Elements List",
		"blockOtherGesturesCheckbox": (
			"Block other NVDA commands while Web Rotor is open "
			"(keys used inside Web Rotor keep working; off by default)"
		),
		"needAtLeastOneCategory": "Please select at least one category.",
		"messageBoxTitle": "Web Rotor",
	},
	"th": {
		"prefsMenuItem": "ตั้งค่าเว็บโรเตอร์... (Web Rotor)",
		"prefsMenuItemHelp": "เลือกและจัดลำดับหมวดหมู่ที่จะแสดงในเว็บโรเตอร์",

		"notBrowseMode": "เว็บโรเตอร์ใช้ได้เฉพาะในเอกสารที่รองรับโหมดเรียกดู (Browse Mode) เท่านั้น",
		"inFocusMode": "กรุณาออกจากโหมดโฟกัส (กด NVDA+Space หรือ Escape) แล้วลองใหม่อีกครั้ง",
		"docOpenWebRotor": "เปิดเว็บโรเตอร์เพื่อสำรวจองค์ประกอบต่างๆ ของหน้าเว็บ เช่น หัวเรื่อง ลิงก์ และจุดสังเกต",
		"docOpenWebRotorSettings": "เปิดหน้าตั้งค่าเว็บโรเตอร์ เพื่อเลือกและจัดลำดับหมวดหมู่ที่จะแสดง",
		"docElementsListOrRotor": "เปิด Elements List มาตรฐานของ NVDA หรือเว็บโรเตอร์ ขึ้นอยู่กับการตั้งค่าเว็บโรเตอร์",

		"rotorTitle": "เว็บโรเตอร์",
		"rotorHint": (
			"ลูกศรขึ้น/ลง: เลื่อนรายการ · พิมพ์ตัวอักษร: กระโดดไปรายการที่ขึ้นต้นด้วยตัวนั้น · "
			"ลูกศรซ้าย/ขวา: เปลี่ยนหมวดหมู่ · Shift+Tab: แท็บหมวดหมู่ · "
			"Alt+ตัวอักษร (อังกฤษหรือไทย): กระโดดไปหมวดหมู่ · Enter: ไปยังตำแหน่งนี้ · Esc: ปิด"
		),
		"rotorHintBlockNotice": " · (ปุ่มลัดอื่นของ NVDA ถูกปิดชั่วคราวขณะหน้าต่างนี้เปิดอยู่)",
		"noCategoriesSelected": "ยังไม่ได้เลือกหมวดหมู่ใดไว้ในการตั้งค่าเว็บโรเตอร์",
		"noLabel": "(ไม่มีป้ายชื่อ)",
		"categoryLabelPlain": "{category} — {total} รายการ",
		"categoryLabelEmpty": "{category} — ไม่พบรายการในหน้านี้",
		"moveToFailed": "ไม่สามารถไปยังตำแหน่งนี้ได้ อาจเป็นเพราะหน้าเว็บมีการเปลี่ยนแปลง",

		"settingsTitle": "ตั้งค่าเว็บโรเตอร์",
		"settingsInstructions": (
			"ติ๊กเลือกหมวดหมู่ที่ต้องการให้ปรากฏในเว็บโรเตอร์ (Control+Windows+U)\n"
			"ใช้ปุ่ม \u201cเลื่อนขึ้น/เลื่อนลง\u201d เพื่อกำหนดลำดับการหมุนด้วยลูกศรซ้าย/ขวา"
		),
		"categoriesListLabel": "หมวดหมู่ (&ห):",
		"moveUpBtn": "เลื่อนขึ้น (&ข)",
		"moveDownBtn": "เลื่อนลง (&ล)",
		"restoreDefaultsBtn": "คืนค่าเริ่มต้น (&ค)",
		"restoredDefaults": "คืนค่าเริ่มต้นแล้ว",
		"languageLabel": "ภาษาที่ใช้แสดงผลเว็บโรเตอร์ (&ภ):",
		"languageEnglish": "English (\u0e2d\u0e31\u0e07\u0e01\u0e24\u0e29)",
		"languageThai": "ไทย",
		"overrideElementsListCheckbox": "ใช้ NVDA+F7 เปิดเว็บโรเตอร์ แทน Elements List มาตรฐานของ NVDA",
		"blockOtherGesturesCheckbox": (
			"บล็อกคำสั่งอื่นของ NVDA ขณะเว็บโรเตอร์เปิดอยู่ "
			"(ปุ่มที่ใช้ในเว็บโรเตอร์ยังทำงานตามปกติ ปิดเป็นค่าเริ่มต้น)"
		),
		"needAtLeastOneCategory": "กรุณาเลือกอย่างน้อยหนึ่งหมวดหมู่",
		"messageBoxTitle": "เว็บโรเตอร์",
	},
}
