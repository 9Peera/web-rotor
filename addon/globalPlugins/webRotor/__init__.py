# -*- coding: utf-8 -*-
# Web Rotor add-on for NVDA
# เว็บโรเตอร์: เมนูหมุนสำหรับสำรวจองค์ประกอบของหน้าเว็บอย่างรวดเร็ว

import wx
import globalPluginHandler
import api
import ui
import gui
import browseMode
from logHandler import log

from . import categories
from . import strings
from .rotorDialog import RotorDialog
from .settingsDialog import RotorSettingsDialog

# กันไม่ให้เปิดหน้าต่างโรเตอร์ซ้อนกันหลายบาน
_activeDialog = None


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	scriptCategory = "Web Rotor"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		categories.registerConfig()

		# เพิ่มรายการ "ตั้งค่าเว็บโรเตอร์..." ไว้ในเมนู Preferences ของ NVDA เพื่อให้ผู้ใช้หาเจอได้ง่าย
		self._settingsMenuItem = None
		try:
			prefsMenu = gui.mainFrame.sysTrayIcon.preferencesMenu
			self._prefsMenu = prefsMenu
			self._settingsMenuItem = prefsMenu.Append(
				wx.ID_ANY,
				strings.tr("prefsMenuItem"),
				strings.tr("prefsMenuItemHelp"),
			)
			gui.mainFrame.sysTrayIcon.Bind(wx.EVT_MENU, self.script_openWebRotorSettings, self._settingsMenuItem)
		except Exception:
			# ถ้าเพิ่มเมนูไม่สำเร็จด้วยเหตุผลใดก็ตาม ผู้ใช้ยังเรียกหน้าตั้งค่าผ่านปุ่มลัดได้ตามปกติ
			self._settingsMenuItem = None

	def terminate(self, *args, **kwargs):
		if self._settingsMenuItem is not None:
			try:
				self._prefsMenu.Remove(self._settingsMenuItem)
			except Exception:
				pass
		super().terminate(*args, **kwargs)

	def _getBrowseModeTreeInterceptor(self):
		focusObj = api.getFocusObject()
		treeInterceptor = getattr(focusObj, "treeInterceptor", None)
		if not isinstance(treeInterceptor, browseMode.BrowseModeDocumentTreeInterceptor):
			return None
		return treeInterceptor

	def _refocusOpenRotor(self):
		"""ถ้าหน้าต่างโรเตอร์เปิดอยู่แล้ว ให้ย้ายโฟกัสกลับไปที่รายการ (NVDA จะอ่านหมวดและรายการปัจจุบัน)
		แทนการเปิดซ้อนหรือเงียบไปเฉยๆ เมื่อผู้ใช้กด Control+Windows+U หรือ NVDA+F7 ซ้ำขณะโรเตอร์เปิดอยู่
		"""
		dlg = _activeDialog
		if dlg is None:
			return False
		try:
			if not dlg or dlg._closeHandled:
				return False
		except Exception:
			return False
		log.info("WebRotor: โรเตอร์เปิดอยู่แล้ว ย้ายโฟกัสกลับไปที่รายการ")

		def refocus():
			try:
				dlg.Raise()
				dlg._focusCurrentList()
			except Exception:
				log.debugWarning("Web Rotor: ย้ายโฟกัสกลับไปที่โรเตอร์ไม่สำเร็จ", exc_info=True)

		wx.CallAfter(refocus)
		return True

	def script_openWebRotor(self, gesture):
		global _activeDialog

		log.info("WebRotor: ผู้ใช้เรียกเปิดเว็บโรเตอร์ (script_openWebRotor)")
		if self._refocusOpenRotor():
			return
		treeInterceptor = self._getBrowseModeTreeInterceptor()
		if treeInterceptor is None:
			ui.message(strings.tr("notBrowseMode"))
			return

		if treeInterceptor.passThrough:
			ui.message(strings.tr("inFocusMode"))
			return

		if _activeDialog is not None:
			try:
				_activeDialog.Close()
			except Exception:
				pass
			_activeDialog = None

		def run():
			global _activeDialog
			gui.mainFrame.prePopup()

			def onClosed():
				global _activeDialog
				_activeDialog = None
				gui.mainFrame.postPopup()

			dlg = RotorDialog(gui.mainFrame, treeInterceptor, onClosedCallback=onClosed)
			_activeDialog = dlg
			dlg.Show()

		wx.CallAfter(run)

	script_openWebRotor.__doc__ = (
		"Opens Web Rotor to explore elements of the current web page, such as headings, links, and landmarks"
	)

	def script_openWebRotorSettings(self, gesture):
		def run():
			gui.mainFrame.prePopup()
			dlg = RotorSettingsDialog(gui.mainFrame)
			dlg.ShowModal()
			dlg.Destroy()
			gui.mainFrame.postPopup()

		wx.CallAfter(run)

	script_openWebRotorSettings.__doc__ = "Opens Web Rotor settings, to choose and reorder the categories shown"

	def script_elementsListOrRotor(self, gesture):
		"""ดักปุ่มลัด NVDA+F7 ของ NVDA เอง
		ถ้าผู้ใช้เปิดตัวเลือก "ใช้ NVDA+F7 เปิดเว็บโรเตอร์" ไว้ในหน้าตั้งค่า จะเปิดเว็บโรเตอร์แทน
		ถ้าไม่ได้เปิดตัวเลือกนี้ไว้ จะเรียกกล่องโต้ตอบ Elements List มาตรฐานของ NVDA ตามปกติ
		เพื่อไม่ให้พฤติกรรมเดิมของ NVDA เปลี่ยนไปโดยที่ผู้ใช้ไม่ได้ตั้งใจ
		"""
		if self._refocusOpenRotor():
			return
		treeInterceptor = self._getBrowseModeTreeInterceptor()

		if categories.getOverrideElementsList() and treeInterceptor is not None:
			log.info("WebRotor: NVDA+F7 ถูกเรียกและตั้งค่าให้เปิดเว็บโรเตอร์แทน Elements List")
			self.script_openWebRotor(gesture)
			return

		# พฤติกรรมมาตรฐาน: เรียกใช้ Elements List เดิมของ NVDA โดยตรง
		# (เป็นเมธอดเดียวกับที่ NVDA ผูกไว้กับ NVDA+F7 ในโหมดเรียกดูอยู่แล้ว)
		if treeInterceptor is not None and hasattr(treeInterceptor, "script_elementsList"):
			treeInterceptor.script_elementsList(gesture)
		# ถ้าไม่ได้อยู่ในโหมดเรียกดูเลย (ไม่มี treeInterceptor) จะไม่ทำอะไร
		# ซึ่งตรงกับพฤติกรรมเดิมของ NVDA+F7 นอกโหมดเรียกดูอยู่แล้ว (ไม่มีการผูกปุ่มนี้ไว้)

	script_elementsListOrRotor.__doc__ = (
		"Opens NVDA's standard Elements List, or Web Rotor, depending on the Web Rotor settings"
	)

	__gestures = {
		"kb:control+windows+u": "openWebRotor",
		"kb:control+windows+shift+u": "openWebRotorSettings",
		"kb:NVDA+f7": "elementsListOrRotor",
	}
