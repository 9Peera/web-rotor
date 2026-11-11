# -*- coding: utf-8 -*-
# Web Rotor add-on for NVDA
# ตรวจหาส่วนเสริมอื่นที่ใช้ปุ่มลัดเดียวกับเว็บโรเตอร์ (เช่น freeAudio 2026.25 ใช้ Control+Windows+U)
# ถ้าชนกัน NVDA จะเรียกคำสั่งของส่วนเสริมไหนก่อนก็ได้ (ลำดับไม่แน่นอน) ทำให้เว็บโรเตอร์ "เรียกไม่ขึ้น"
# โมดูลนี้แค่ตรวจและรายงาน การแก้ (ถอดปุ่มลัดออกจากส่วนเสริมอื่น) ทำเมื่อผู้ใช้กดปุ่มยืนยันเองเท่านั้น

import os
import sys

import addonHandler
import globalPluginHandler
import inputCore
from logHandler import log

# ปุ่มลัดของเว็บโรเตอร์ที่ต้องตรวจ (NVDA+F7 ไม่ตรวจ เพราะเป็นปุ่มของ NVDA เองและจะทำงานแทนเมื่อผู้ใช้เลือกเท่านั้น)
OWN_GESTURES = (
	"kb:control+windows+u",
	"kb:control+windows+shift+u",
)


def _normalize(gestureId):
	try:
		return inputCore.normalizeGestureIdentifier(gestureId)
	except Exception:
		return gestureId.lower()


def _displayGesture(gestureId):
	try:
		return inputCore.getDisplayTextForGestureIdentifier(gestureId)[1]
	except Exception:
		return gestureId.split(":", 1)[-1]


def _userEntries(gestureId):
	"""คืนรายการ (คลาส, ชื่อสคริปต์) ที่ผู้ใช้ผูก/ถอดไว้กับปุ่มนี้ใน gestures.ini"""
	try:
		return [
			(cls, scriptName)
			for cls, scriptName in inputCore.manager.userGestureMap.getScriptsForGesture(gestureId)
			if cls is not None
		]
	except Exception:
		return []


def _addonName(cls):
	"""หาชื่อส่วนเสริมที่เป็นเจ้าของคลาสนี้ (ใช้ summary ใน manifest) ถ้าหาไม่ได้ใช้ชื่อโมดูลแทน"""
	fallback = cls.__module__.split(".")[1] if "." in cls.__module__ else cls.__module__
	try:
		modFile = os.path.normcase(os.path.abspath(sys.modules[cls.__module__].__file__))
		for addon in addonHandler.getRunningAddons():
			addonPath = os.path.normcase(os.path.abspath(addon.path)) + os.sep
			if modFile.startswith(addonPath):
				return addon.manifest.get("summary") or addon.name
	except Exception:
		pass
	return fallback


def _commandName(plugin, scriptName):
	func = getattr(plugin, "script_%s" % scriptName, None)
	doc = (getattr(func, "__doc__", None) or "").strip()
	return doc.splitlines()[0] if doc else scriptName


def _isOwnGestureActive(ownPlugin, gestureId):
	"""ถ้าผู้ใช้ถอดปุ่มนี้ออกจากเว็บโรเตอร์เองแล้ว ก็ไม่นับว่าชนกัน"""
	for cls, scriptName in _userEntries(gestureId):
		if isinstance(ownPlugin, cls) and scriptName is None:
			return False
	return True


def findConflicts(ownPlugin):
	"""คืนรายการปุ่มลัดที่ชนกับส่วนเสริมอื่น แต่ละรายการเป็น dict
	(gesture, gestureText, cls, scriptName, fromUserMap, addon, command)
	ห้ามโยน exception ออกไป: ถ้าตรวจไม่ได้ให้คืนรายการว่าง
	"""
	results = []
	try:
		plugins = [p for p in list(globalPluginHandler.runningPlugins) if p is not ownPlugin]
		for rawId in OWN_GESTURES:
			gestureId = _normalize(rawId)
			if not _isOwnGestureActive(ownPlugin, gestureId):
				continue
			userEntries = _userEntries(gestureId)
			for plugin in plugins:
				cls = type(plugin)
				scriptName = None
				fromUserMap = False
				handledByUserMap = False
				for entryCls, entryScript in userEntries:
					if isinstance(plugin, entryCls):
						# ผู้ใช้ตั้งค่าไว้เองใน Input Gestures: None = ถอดออกแล้ว, ชื่อสคริปต์ = ผูกไว้เอง
						handledByUserMap = True
						scriptName = entryScript
						fromUserMap = entryScript is not None
						break
				if not handledByUserMap:
					# _gestureMap ของ NVDA เก็บ "ฟังก์ชัน script_xxx" ไม่ใช่ชื่อสคริปต์
					func = (getattr(plugin, "_gestureMap", None) or {}).get(gestureId)
					funcName = getattr(func, "__name__", "") or ""
					if funcName.startswith("script_"):
						scriptName = funcName[len("script_"):]
				if not scriptName:
					continue
				results.append({
					"gesture": gestureId,
					"gestureText": _displayGesture(gestureId),
					"cls": cls,
					"scriptName": scriptName,
					"fromUserMap": fromUserMap,
					"addon": _addonName(cls),
					"command": _commandName(plugin, scriptName),
				})
	except Exception:
		log.debugWarning("Web Rotor: ตรวจปุ่มลัดที่ชนกันไม่สำเร็จ", exc_info=True)
		return []
	return results


def signature(conflicts):
	"""ข้อความสั้นๆ แทนชุดปุ่มที่ชนกัน ใช้จำว่าเคยแจ้งผู้ใช้เรื่องชุดนี้แล้วหรือยัง"""
	return ";".join(sorted(
		"%s|%s.%s" % (c["gesture"], c["cls"].__module__, c["cls"].__name__) for c in conflicts
	))


def fixConflicts(conflicts):
	"""ถอดปุ่มลัดที่ชนกันออกจากส่วนเสริมอื่น ผ่านการตั้งค่า Input Gestures ของผู้ใช้ (gestures.ini)
	คำสั่งของส่วนเสริมนั้นยังอยู่ ผู้ใช้กำหนดปุ่มใหม่ให้ได้ใน Input Gestures
	เรียกเมื่อผู้ใช้กดยืนยันเท่านั้น คืนค่า True ถ้าสำเร็จ
	"""
	try:
		userMap = inputCore.manager.userGestureMap
		for c in conflicts:
			module = c["cls"].__module__
			className = c["cls"].__name__
			if c["fromUserMap"]:
				try:
					userMap.remove(c["gesture"], module, className, c["scriptName"])
				except Exception:
					pass
			userMap.add(c["gesture"], module, className, None)
		userMap.save()
		log.info("Web Rotor: ถอดปุ่มลัดที่ชนกันออกจากส่วนเสริมอื่นแล้ว: %s" % signature(conflicts))
		return True
	except Exception:
		log.error("Web Rotor: แก้ปุ่มลัดที่ชนกันไม่สำเร็จ", exc_info=True)
		return False
