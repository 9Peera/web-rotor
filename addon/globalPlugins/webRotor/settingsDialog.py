# -*- coding: utf-8 -*-
# Web Rotor add-on for NVDA
# หน้าต่างตั้งค่า: เลือกภาษา, เลือกเปิด/ปิดหมวดหมู่, จัดลำดับการหมุน, ตัวเลือกแทนที่ NVDA+F7

import wx
import gui
import ui
from logHandler import log

try:
	# รายการช่องติ๊กของ NVDA เองที่แก้ให้โปรแกรมอ่านหน้าจออ่านสถานะ "เลือก/ไม่เลือก" ได้
	from gui.nvdaControls import CustomCheckListBox as _CheckListBox
except Exception:
	_CheckListBox = wx.CheckListBox

from . import categories as cat
from . import conflicts
from . import strings


class RotorSettingsDialog(wx.Dialog):
	"""กล่องโต้ตอบตั้งค่าเว็บโรเตอร์
	- เลือกภาษาที่ใช้แสดงผลของเว็บโรเตอร์ (ไทย/อังกฤษ)
	- ติ๊กถูก/ไม่ติ๊ก เพื่อเปิด/ปิดการแสดงหมวดหมู่นั้นในโรเตอร์
	- ปุ่มเลื่อนขึ้น/ลง เพื่อจัดลำดับการหมุน (ลำดับในลิสต์ = ลำดับตอนกดลูกศรขวาในโรเตอร์)
	- ตัวเลือกให้ NVDA+F7 เปิดเว็บโรเตอร์แทน Elements List เดิม
	- ปุ่มคืนค่าเริ่มต้น
	การเปลี่ยนภาษาจะมีผลตั้งแต่ครั้งถัดไปที่เปิดเว็บโรเตอร์หรือหน้าตั้งค่านี้
	"""

	def __init__(self, parent, plugin=None):
		self._plugin = plugin
		# ปุ่มลัดที่ชนกับส่วนเสริมอื่น (ตรวจก่อนสร้างหน้าจอ เพื่อแสดงส่วนแก้ไขเฉพาะเมื่อมีปัญหา)
		self._conflicts = conflicts.findConflicts(plugin) if plugin is not None else []
		super().__init__(
			parent,
			title=strings.tr("settingsTitle"),
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)

		enabled = cat.getEnabledCategories()
		# แสดงหมวดที่เปิดใช้งานอยู่ก่อน (ตามลำดับที่ตั้งไว้) แล้วตามด้วยหมวดที่ยังไม่เปิด
		self._itemTypes = list(enabled) + [i for i in cat.MASTER_ORDER if i not in enabled]
		# หมายเหตุ: หน้าตั้งค่านี้ไม่บล็อกคำสั่งอื่นของ NVDA (ตัวเลือกบล็อกมีผลเฉพาะหน้าต่างโรเตอร์)
		# เวอร์ชัน 1.8.0 และก่อนหน้าบล็อกทุกปุ่มในหน้านี้ด้วย ทำให้ NVDA เงียบและใช้งานหน้าตั้งค่าไม่ได้

		self._buildUI(enabled)

	def _buildUI(self, enabled):
		mainSizer = wx.BoxSizer(wx.VERTICAL)

		instructions = wx.StaticText(self, label=strings.tr("settingsInstructions"))
		mainSizer.Add(instructions, 0, wx.ALL | wx.EXPAND, 8)

		# --- ตัวเลือกภาษา ---
		self.languageRadio = wx.RadioBox(
			self,
			label=strings.tr("languageLabel"),
			choices=[strings.tr("languageEnglish"), strings.tr("languageThai")],
			majorDimension=1,
			style=wx.RA_SPECIFY_COLS,
		)
		self.languageRadio.SetSelection(1 if strings.getLang() == "th" else 0)
		mainSizer.Add(self.languageRadio, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 8)

		# --- รายการหมวดหมู่ + ปุ่มจัดลำดับ ---
		bodySizer = wx.BoxSizer(wx.HORIZONTAL)

		listLabel = wx.StaticText(self, label=strings.tr("categoriesListLabel"))
		listSizer = wx.BoxSizer(wx.VERTICAL)
		listSizer.Add(listLabel, 0, wx.BOTTOM, 4)

		self.checkList = _CheckListBox(
			self,
			choices=[cat.getLabel(i) for i in self._itemTypes],
		)
		self.checkList.SetMinSize((420, 300))
		for idx, itemType in enumerate(self._itemTypes):
			self.checkList.Check(idx, itemType in enabled)
		listSizer.Add(self.checkList, 1, wx.EXPAND)
		bodySizer.Add(listSizer, 1, wx.ALL | wx.EXPAND, 8)

		btnSizer = wx.BoxSizer(wx.VERTICAL)
		self.upBtn = wx.Button(self, label=strings.tr("moveUpBtn"))
		self.downBtn = wx.Button(self, label=strings.tr("moveDownBtn"))
		btnSizer.Add(self.upBtn, 0, wx.ALL | wx.EXPAND, 4)
		btnSizer.Add(self.downBtn, 0, wx.ALL | wx.EXPAND, 4)
		btnSizer.AddSpacer(16)
		self.defaultsBtn = wx.Button(self, label=strings.tr("restoreDefaultsBtn"))
		btnSizer.Add(self.defaultsBtn, 0, wx.ALL | wx.EXPAND, 4)
		bodySizer.Add(btnSizer, 0, wx.TOP, 30)

		mainSizer.Add(bodySizer, 1, wx.EXPAND)

		self.overrideCheckbox = wx.CheckBox(self, label=strings.tr("overrideElementsListCheckbox"))
		self.overrideCheckbox.SetValue(cat.getOverrideElementsList())
		mainSizer.Add(self.overrideCheckbox, 0, wx.LEFT | wx.RIGHT | wx.TOP, 8)

		self.blockGesturesCheckbox = wx.CheckBox(self, label=strings.tr("blockOtherGesturesCheckbox"))
		self.blockGesturesCheckbox.SetValue(cat.getBlockOtherGestures())
		mainSizer.Add(self.blockGesturesCheckbox, 0, wx.ALL, 8)

		# --- ปุ่มลัดที่ชนกับส่วนเสริมอื่น (แสดงเฉพาะเมื่อพบ) ---
		# ใช้ช่องข้อความแบบอ่านอย่างเดียว เพื่อให้กด Tab ไปถึงและ NVDA อ่านรายละเอียดได้
		self.conflictsLabel = None
		self.conflictsText = None
		self.fixConflictsBtn = None
		if self._conflicts:
			self.conflictsLabel = wx.StaticText(self, label=strings.tr("conflictsLabel"))
			mainSizer.Add(self.conflictsLabel, 0, wx.LEFT | wx.RIGHT, 8)
			self.conflictsText = wx.TextCtrl(
				self,
				value="\n".join(self._conflictLines()),
				style=wx.TE_MULTILINE | wx.TE_READONLY,
				size=(420, 60),
			)
			mainSizer.Add(self.conflictsText, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 8)
			self.fixConflictsBtn = wx.Button(self, label=strings.tr("fixConflictsBtn"))
			mainSizer.Add(self.fixConflictsBtn, 0, wx.ALL, 8)
			self.fixConflictsBtn.Bind(wx.EVT_BUTTON, self._onFixConflicts)

		line = wx.StaticLine(self)
		mainSizer.Add(line, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

		okCancelSizer = self.CreateButtonSizer(wx.OK | wx.CANCEL)
		mainSizer.Add(okCancelSizer, 0, wx.ALL | wx.ALIGN_RIGHT, 8)

		self.SetSizerAndFit(mainSizer)
		self.CentreOnScreen()

		self.upBtn.Bind(wx.EVT_BUTTON, lambda evt: self._move(-1))
		self.downBtn.Bind(wx.EVT_BUTTON, lambda evt: self._move(1))
		self.defaultsBtn.Bind(wx.EVT_BUTTON, self._onDefaults)
		self.Bind(wx.EVT_BUTTON, self._onOk, id=wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self._onCancel, id=wx.ID_CANCEL)

		if self._itemTypes:
			self.checkList.SetSelection(0)
		self.checkList.SetFocus()

	def _move(self, step):
		sel = self.checkList.GetSelection()
		if sel == wx.NOT_FOUND:
			return
		newIndex = sel + step
		if newIndex < 0 or newIndex >= len(self._itemTypes):
			return

		checkedStates = [self.checkList.IsChecked(i) for i in range(len(self._itemTypes))]

		self._itemTypes[sel], self._itemTypes[newIndex] = self._itemTypes[newIndex], self._itemTypes[sel]
		checkedStates[sel], checkedStates[newIndex] = checkedStates[newIndex], checkedStates[sel]

		self._refreshList(checkedStates)
		self.checkList.SetSelection(newIndex)
		self.checkList.SetFocus()

	def _refreshList(self, checkedStates):
		self.checkList.Set([cat.getLabel(i) for i in self._itemTypes])
		for idx, checked in enumerate(checkedStates):
			self.checkList.Check(idx, checked)

	def _onDefaults(self, evt):
		defaults = list(cat.DEFAULT_ENABLED)
		self._itemTypes = defaults + [i for i in cat.MASTER_ORDER if i not in defaults]
		self._refreshList([itemType in defaults for itemType in self._itemTypes])
		if self._itemTypes:
			self.checkList.SetSelection(0)
		self.checkList.SetFocus()
		ui.message(strings.tr("restoredDefaults"))

	def _conflictLines(self):
		return [
			strings.tr("conflictLine", shortcut=c["gestureText"], addon=c["addon"], command=c["command"])
			for c in self._conflicts
		]

	def _onFixConflicts(self, evt):
		"""ถอดปุ่มลัดที่ชนกันออกจากส่วนเสริมอื่น หลังจากผู้ใช้ยืนยันแล้วเท่านั้น"""
		answer = gui.messageBox(
			strings.tr("fixConflictsConfirm", lines="\n".join(self._conflictLines())),
			strings.tr("messageBoxTitle"),
			wx.YES_NO | wx.ICON_QUESTION,
			self,
		)
		if answer != wx.YES:
			return
		if not conflicts.fixConflicts(self._conflicts):
			ui.message(strings.tr("conflictsFixFailed"))
			return
		# ย้ายโฟกัสออกก่อนซ่อนปุ่ม ไม่ให้โฟกัสหายไปกับปุ่มที่ถูกซ่อน
		self.checkList.SetFocus()
		for ctrl in (self.conflictsLabel, self.conflictsText, self.fixConflictsBtn):
			if ctrl is not None:
				ctrl.Hide()
		self._conflicts = []
		self.Layout()
		self.Fit()
		ui.message(strings.tr("conflictsFixed"))

	def _onCancel(self, evt):
		evt.Skip()

	def _onOk(self, evt):
		enabledOrdered = [
			itemType
			for idx, itemType in enumerate(self._itemTypes)
			if self.checkList.IsChecked(idx)
		]
		if not enabledOrdered:
			gui.messageBox(
				strings.tr("needAtLeastOneCategory"),
				strings.tr("messageBoxTitle"),
				wx.OK | wx.ICON_WARNING,
				self,
			)
			return
		cat.setEnabledCategories(enabledOrdered)
		cat.setOverrideElementsList(self.overrideCheckbox.GetValue())
		cat.setBlockOtherGestures(self.blockGesturesCheckbox.GetValue())
		strings.setLang("th" if self.languageRadio.GetSelection() == 1 else "en")
		evt.Skip()
