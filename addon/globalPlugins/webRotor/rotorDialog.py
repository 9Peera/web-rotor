# -*- coding: utf-8 -*-
# Web Rotor add-on for NVDA
# หน้าต่างเมนูหมุน (Rotor) สำหรับสำรวจองค์ประกอบของหน้าเว็บ พร้อมช่องกรองรายการ

import wx
import ui
import inputCore
from logHandler import log

from . import categories as cat
from . import strings

MAX_LABEL_LENGTH = 100  # ตัดข้อความป้ายชื่อที่ยาวเกินไปในลิสต์
MAX_ITEMS_PER_CATEGORY = 2000  # เพดานจำนวนรายการต่อหมวดหมู่ กันไม่ให้หน้าเว็บที่ใหญ่มากทำให้ค้าง


class RotorDialog(wx.Dialog):
	"""กล่องโต้ตอบเว็บโรเตอร์
	Ctrl+ลูกศรซ้าย/ขวา: เปลี่ยนหมวดหมู่ (ใช้งานได้ทั้งตอนโฟกัสอยู่ที่ช่องกรองและที่รายการ)
	ลูกศรซ้าย/ขวา (เมื่อโฟกัสอยู่ที่รายการ): เปลี่ยนหมวดหมู่เช่นกัน เพื่อความสะดวก
	ลูกศรขึ้น/ลง: เลื่อนดูรายการภายในหมวดหมู่ปัจจุบัน
	พิมพ์ตัวอักษรในช่องกรอง: กรองรายการของหมวดหมู่ปัจจุบันแบบเรียลไทม์
	ลูกศรลง (จากช่องกรอง): ย้ายโฟกัสไปยังรายการแรกที่กรองได้
	Enter/Space: กระโดดไปยังตำแหน่งที่เลือกในเอกสาร แล้วปิดกล่องโต้ตอบ
	Escape: ปิดกล่องโต้ตอบโดยไม่ทำอะไร

	ขณะที่กล่องโต้ตอบนี้เปิดอยู่ ปุ่มลัด/คำสั่งอื่นๆ ของ NVDA (นอกเหนือจากการนำทางภายในโรเตอร์เอง)
	จะถูกปิดใช้งานชั่วคราว เพื่อป้องกันการกดพลาดไปโดนคำสั่งอื่นระหว่างใช้งาน
	"""

	def __init__(self, parent, treeInterceptor, onClosedCallback=None):
		super().__init__(
			parent,
			title=strings.tr("rotorTitle"),
			style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
		)
		self.treeInterceptor = treeInterceptor
		self._onClosedCallback = onClosedCallback
		self._closeHandled = False
		# โหลดรายการหมวดหมู่ที่ผู้ใช้เปิดใช้งานไว้ (เรียงตามลำดับที่ตั้งค่า) ทุกครั้งที่เปิดโรเตอร์
		self.categories = [(cat.getLabel(itemType), itemType) for itemType in cat.getEnabledCategories()]
		self.categoryIndex = 0
		self._itemsCache = {}  # itemType -> รายการ QuickNavItem ทั้งหมดที่ดึงมาแล้ว (ยังไม่กรอง)
		self._currentItems = []  # รายการหลังกรองของหมวดหมู่ปัจจุบัน ตรงกับแถวใน listBox
		self._gestureBlockActive = False

		# ตารางคีย์ลัด Alt+ตัวอักษร -> ลำดับหมวดหมู่ (เฉพาะหมวดที่เปิดใช้งานอยู่จริงในโรเตอร์นี้)
		# ตัวอักษรจะเปลี่ยนไปตามภาษาที่ตั้งค่าไว้โดยอัตโนมัติ (strings.CATEGORY_SHORTCUTS)
		shortcutTable = strings.CATEGORY_SHORTCUTS.get(strings.getLang(), strings.CATEGORY_SHORTCUTS[strings.DEFAULT_LANG])
		self._categoryShortcutMap = {}
		for idx, (_label, itemType) in enumerate(self.categories):
			letter = shortcutTable.get(itemType)
			if letter:
				self._categoryShortcutMap[letter.upper()] = idx

		self._buildUI()
		self.Bind(wx.EVT_CLOSE, self._onClose)
		self._blockOtherGestures()
		log.info("WebRotor: เปิดหน้าต่างเว็บโรเตอร์ (หมวดหมู่ที่เปิดใช้งาน: %s)" % (
			", ".join(itemType for _label, itemType in self.categories)))
		# เผื่อไว้กันกรณีเกิดข้อผิดพลาดไม่คาดคิดที่ทำให้ EVT_CLOSE ไม่ถูกเรียก (เช่น หน้าต่างถูกทำลาย
		# ด้วยวิธีอื่นนอกเหนือจาก Close()) - ตั้งตัวจับเวลาเพื่อยกเลิกการบล็อกปุ่มลัดอัตโนมัติหลัง 5 นาที
		# เพื่อไม่ให้ปุ่มลัดอื่นของ NVDA ถูกปิดใช้งานค้างอย่างไม่มีกำหนด
		self._watchdogTimer = wx.CallLater(5 * 60 * 1000, self._unblockOtherGestures)

		if not self.categories:
			# กรณีนี้ไม่ควรเกิดขึ้นเพราะ categories.py มีค่า default สำรองไว้เสมอ แต่กันไว้เพื่อความปลอดภัย
			ui.message(strings.tr("noCategoriesSelected"))
			wx.CallAfter(self.Close)
			return

		self._loadCategory(self.categoryIndex, announce=False)
		self.filterCtrl.SetFocus()

	def _buildUI(self):
		mainSizer = wx.BoxSizer(wx.VERTICAL)

		filterSizer = wx.BoxSizer(wx.HORIZONTAL)
		filterLabelText = wx.StaticText(self, label=strings.tr("filterLabel"))
		filterSizer.Add(filterLabelText, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
		self.filterCtrl = wx.TextCtrl(self)
		filterSizer.Add(self.filterCtrl, 1, wx.EXPAND)
		mainSizer.Add(filterSizer, 0, wx.ALL | wx.EXPAND, 8)

		self.categoryLabel = wx.StaticText(self, label="")
		mainSizer.Add(self.categoryLabel, 0, wx.LEFT | wx.RIGHT | wx.EXPAND, 8)

		self.listBox = wx.ListBox(self, style=wx.LB_SINGLE)
		self.listBox.SetMinSize((480, 320))
		mainSizer.Add(self.listBox, 1, wx.ALL | wx.EXPAND, 8)

		hint = wx.StaticText(self, label=(
			strings.tr("rotorHint")
			+ strings.tr("rotorHintShortcut")
			+ (strings.tr("rotorHintBlockNotice") if cat.getBlockOtherGestures() else "")
		))
		mainSizer.Add(hint, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		self.SetSizerAndFit(mainSizer)
		self.CentreOnScreen()

		self.filterCtrl.Bind(wx.EVT_TEXT, self._onFilterText)
		self.filterCtrl.Bind(wx.EVT_KEY_DOWN, self._onFilterKeyDown)
		self.listBox.Bind(wx.EVT_KEY_DOWN, self._onListKeyDown)
		self.listBox.Bind(wx.EVT_LISTBOX_DCLICK, self._onActivate)
		self.Bind(wx.EVT_CHAR_HOOK, self._onCharHook)

	def _onCharHook(self, evt):
		# ใช้ CHAR_HOOK เพื่อดักคีย์สำคัญได้แน่นอนไม่ว่าโฟกัสจะอยู่ที่คอนโทรลใด (ช่องกรองหรือรายการ)
		code = evt.GetKeyCode()

		if code == wx.WXK_ESCAPE:
			self.Close()
			return

		# Enter/ปุ่ม Numpad Enter: กระโดดไปยังตำแหน่งที่เลือกอยู่ในขณะนี้เสมอ ไม่ว่าโฟกัสจะอยู่ตรงไหน
		# (นอกเหนือจากที่แต่ละคอนโทรลจัดการเองอยู่แล้ว จุดนี้เป็นการรับประกันอีกชั้นให้ Enter ทำงาน
		# เหมือน Space ได้แน่นอนในทุกกรณี)
		if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and not evt.AltDown():
			self._onActivate(evt)
			return

		# Alt+ตัวอักษร: กระโดดตรงไปยังหมวดหมู่ที่ตรงกับตัวอักษรนั้นทันที (ตัวอักษรเปลี่ยนตามภาษาที่ตั้งค่าไว้)
		if evt.AltDown() and not evt.ControlDown() and self._categoryShortcutMap:
			uni = evt.GetUnicodeKey()
			if uni and uni != wx.WXK_NONE:
				letter = chr(uni).upper()
				idx = self._categoryShortcutMap.get(letter)
				if idx is not None:
					self._switchToCategoryIndex(idx)
					return

		evt.Skip()

	def _onClose(self, evt):
		# ป้องกันการทำงานซ้ำถ้า EVT_CLOSE ถูกยิงมากกว่าหนึ่งครั้งด้วยเหตุผลใดก็ตาม
		if self._closeHandled:
			evt.Skip()
			return
		self._closeHandled = True

		log.info("WebRotor: ปิดหน้าต่างเว็บโรเตอร์")
		if getattr(self, "_watchdogTimer", None) is not None and self._watchdogTimer.IsRunning():
			self._watchdogTimer.Stop()
		self._unblockOtherGestures()

		if self._onClosedCallback is not None:
			try:
				self._onClosedCallback()
			except Exception:
				log.debugWarning("Web Rotor: onClosedCallback ทำงานผิดพลาด", exc_info=True)

		evt.Skip()
		# สำคัญ: wx.Dialog แบบ non-modal (เปิดด้วย Show()) จะไม่ถูกทำลายอัตโนมัติเสมอไป
		# แม้เรียก evt.Skip() แล้วก็ตาม - ต้องสั่ง Destroy() เองอย่างชัดเจน เพื่อไม่ให้ค้างเป็น
		# หน้าต่างที่ถูกซ่อนไว้เฉยๆ (ซึ่งจะทำให้การเรียก gui.mainFrame.prePopup()/postPopup()
		# ของ NVDA ไม่สมดุลกันในการเปิดโรเตอร์ครั้งถัดไป)
		wx.CallAfter(self.Destroy)

	def _blockOtherGestures(self):
		"""บล็อกไม่ให้ปุ่มลัด/คำสั่งอื่นๆ ของ NVDA (นอกเหนือจากของเว็บโรเตอร์เอง) ทำงาน
		ขณะที่กล่องโต้ตอบนี้เปิดอยู่ เพื่อป้องกันการกดพลาดไปโดนคำสั่งอื่นระหว่างใช้งานโรเตอร์
		การนำทางภายในโรเตอร์เอง (ลูกศร, Enter, Esc, การพิมพ์กรอง) ใช้กลไกของ wx โดยตรง
		ไม่ผ่านระบบ gesture ของ NVDA จึงไม่ได้รับผลกระทบจากการบล็อกนี้

		ฟีเจอร์นี้เป็นทางเลือก (ปิดเป็นค่าเริ่มต้น) เนื่องจากอาจชนกับส่วนเสริมอื่นบางตัว
		จนทำให้ NVDA ค้างได้ในบางเครื่อง เปิดใช้งานได้ที่หน้าตั้งค่าเว็บโรเตอร์
		"""
		if not cat.getBlockOtherGestures():
			self._gestureBlockActive = False
			return
		try:
			inputCore.decide_executeGesture.register(self._decideExecuteGesture)
			self._gestureBlockActive = True
			log.info("WebRotor: เริ่มบล็อกปุ่มลัดอื่นของ NVDA (decide_executeGesture registered)")
		except Exception:
			# NVDA บางเวอร์ชันอาจไม่มี extension point นี้ - ถ้าเกิดขึ้น จะไม่บล็อกปุ่มลัดอื่น
			# แต่โรเตอร์ยังใช้งานได้ตามปกติ
			log.debugWarning("Web Rotor: ไม่สามารถบล็อกปุ่มลัดอื่นของ NVDA ได้", exc_info=True)
			self._gestureBlockActive = False

	def _unblockOtherGestures(self):
		if self._gestureBlockActive:
			try:
				inputCore.decide_executeGesture.unregister(self._decideExecuteGesture)
				log.info("WebRotor: ยกเลิกการบล็อกปุ่มลัดอื่นของ NVDA แล้ว (decide_executeGesture unregistered)")
			except Exception:
				log.debugWarning("Web Rotor: ยกเลิกการบล็อกปุ่มลัดไม่สำเร็จ", exc_info=True)
			self._gestureBlockActive = False

	def _decideExecuteGesture(self, gesture):
		# คืนค่า False เสมอ เพื่อยกเลิกการทำงานของปุ่มลัด/คำสั่งใดๆ ของ NVDA
		# ขณะที่กล่องโต้ตอบเว็บโรเตอร์นี้เปิดอยู่
		return False

	def _onFilterKeyDown(self, evt):
		code = evt.GetKeyCode()
		if code == wx.WXK_DOWN:
			# ย้ายโฟกัสไปยังรายการแรกในลิสต์ที่กรองได้ (ถ้ามี)
			if self.listBox.GetCount() > 0:
				self.listBox.SetFocus()
				if self.listBox.GetSelection() == wx.NOT_FOUND:
					self.listBox.SetSelection(0)
			return
		if code == wx.WXK_LEFT and evt.ControlDown():
			self._switchCategory(-1)
			return
		if code == wx.WXK_RIGHT and evt.ControlDown():
			self._switchCategory(1)
			return
		if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER):
			# Enter จากช่องกรอง = ไปยังรายการแรกที่กรองได้ทันที
			self._onActivate(evt)
			return
		evt.Skip()

	def _onListKeyDown(self, evt):
		code = evt.GetKeyCode()
		if code == wx.WXK_LEFT:
			self._switchCategory(-1)
		elif code == wx.WXK_RIGHT:
			self._switchCategory(1)
		elif code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_SPACE):
			self._onActivate(evt)
		else:
			# ปล่อยให้ ListBox จัดการปุ่มขึ้น/ลง/Home/End ตามปกติ
			evt.Skip()

	def _onFilterText(self, evt):
		self._applyFilter()

	def _switchCategory(self, step):
		if not self.categories:
			return
		newIndex = (self.categoryIndex + step) % len(self.categories)
		self._switchToCategoryIndex(newIndex)

	def _switchToCategoryIndex(self, index):
		if not self.categories:
			return
		if index == self.categoryIndex:
			# อยู่ที่หมวดนี้แล้ว (เช่น กดคีย์ลัดซ้ำของหมวดเดิม) ไม่ต้องทำอะไรซ้ำ
			return
		self.categoryIndex = index
		log.info("WebRotor: สลับไปหมวดหมู่ '%s'" % self.categories[self.categoryIndex][1])
		self._loadCategory(self.categoryIndex, announce=True)

	def _ensureItemsLoaded(self, itemType):
		items = self._itemsCache.get(itemType)
		if items is None:
			log.info("WebRotor: เริ่มดึงรายการประเภท '%s'" % itemType)
			items = []
			truncated = False
			try:
				for item in self.treeInterceptor._iterNodesByType(itemType):
					items.append(item)
					if len(items) >= MAX_ITEMS_PER_CATEGORY:
						# กันไว้ไม่ให้หน้าเว็บที่มีองค์ประกอบจำนวนมหาศาลทำให้การวนลูปนี้ค้างนาน
						# เกินไปบน main thread ของ NVDA
						truncated = True
						log.info(
							"WebRotor: ประเภท '%s' มีรายการเกิน %d รายการ ตัดไว้ที่ %d รายการแรก"
							% (itemType, MAX_ITEMS_PER_CATEGORY, MAX_ITEMS_PER_CATEGORY)
						)
						break
			except NotImplementedError:
				# เอกสารประเภทนี้ไม่รองรับ itemType นี้
				items = []
			except Exception:
				log.debugWarning("Web Rotor: ไม่สามารถดึงรายการประเภท %s ได้" % itemType, exc_info=True)
				items = []
			log.info("WebRotor: ดึงรายการประเภท '%s' เสร็จแล้ว จำนวน %d รายการ (truncated=%s)" % (
				itemType, len(items), truncated))
			self._itemsCache[itemType] = items
		return items

	def _loadCategory(self, index, announce=True):
		label, itemType = self.categories[index]
		allItems = self._ensureItemsLoaded(itemType)
		self._applyFilter()

		if announce:
			query = self.filterCtrl.GetValue().strip()
			total = len(allItems)
			shown = len(self._currentItems)
			if query:
				if shown:
					ui.message(strings.tr("announceFiltered", category=label, shown=shown, total=total))
				else:
					ui.message(strings.tr("announceFilteredNone", category=label))
			else:
				if total:
					ui.message(strings.tr("announcePlain", category=label, total=total))
				else:
					ui.message(strings.tr("announceEmpty", category=label))

	def _applyFilter(self):
		"""กรองรายการของหมวดหมู่ปัจจุบันตามข้อความในช่องกรอง แล้วรีเฟรช listBox"""
		if not self.categories:
			return
		_label, itemType = self.categories[self.categoryIndex]
		allItems = self._itemsCache.get(itemType, [])
		query = self.filterCtrl.GetValue().strip().lower()

		if query:
			filtered = [it for it in allItems if query in (it.label or "").lower()]
		else:
			filtered = allItems

		self._currentItems = filtered
		self._refreshListBox()

		label = cat.getLabel(itemType)
		if query:
			self.categoryLabel.SetLabel(
				strings.tr("categoryLabelFiltered", category=label, shown=len(filtered), total=len(allItems))
			)
		else:
			self.categoryLabel.SetLabel(
				strings.tr("categoryLabelPlain", category=label, total=len(allItems))
			)

	def _refreshListBox(self):
		self.listBox.Freeze()
		self.listBox.Clear()
		if self._currentItems:
			labels = []
			for it in self._currentItems:
				text = (it.label or "").strip()
				if not text:
					text = strings.tr("noLabel")
				if len(text) > MAX_LABEL_LENGTH:
					text = text[:MAX_LABEL_LENGTH] + "\u2026"
				labels.append(text)
			self.listBox.InsertItems(labels, 0)
			self.listBox.SetSelection(0)
		self.listBox.Thaw()

	def _onActivate(self, evt):
		sel = self.listBox.GetSelection()
		if sel == wx.NOT_FOUND or sel >= len(self._currentItems):
			return
		item = self._currentItems[sel]
		log.info("WebRotor: เลือกรายการลำดับที่ %d ในหมวดปัจจุบัน กำลังปิดหน้าต่างและย้ายตำแหน่ง" % sel)
		self.Close()
		# หน่วงเวลาเล็กน้อยเพื่อให้กล่องโต้ตอบปิดและคืนโฟกัสให้เอกสารก่อน
		# แล้วจึงค่อยย้ายเคอร์เซอร์ไปยังตำแหน่งที่เลือก
		wx.CallLater(120, self._safeMoveTo, item)

	def _safeMoveTo(self, item):
		try:
			item.moveTo()
			log.info("WebRotor: ย้ายตำแหน่งสำเร็จ")
		except Exception:
			log.debugWarning("Web Rotor: ย้ายตำแหน่งไม่สำเร็จ", exc_info=True)
			ui.message(strings.tr("moveToFailed"))
