# -*- coding: utf-8 -*-
# Web Rotor add-on for NVDA
# หน้าต่างเมนูหมุน (Rotor) สำหรับสำรวจองค์ประกอบของหน้าเว็บ
# แต่ละหมวดหมู่เป็นแท็บหนึ่งแท็บ (wx.Notebook) และในแต่ละแท็บมีรายการ (ListBox) ของหมวดนั้น

import time

import wx
import ui
import tones
import inputCore
from logHandler import log

from . import categories as cat
from . import strings

MAX_LABEL_LENGTH = 100  # ตัดข้อความป้ายชื่อที่ยาวเกินไปในลิสต์
MAX_ITEMS_PER_CATEGORY = 2000  # เพดานจำนวนรายการต่อหมวดหมู่ กันไม่ให้หน้าเว็บที่ใหญ่มากทำให้ค้าง
TYPE_AHEAD_TIMEOUT = 1.0  # วินาที: พิมพ์ต่อกันภายในเวลานี้จะค้นหาเป็นคำ (เช่น "ติ" -> "ติดต่อเรา")
MAPVK_VK_TO_CHAR = 2


def _layoutCharForKey(vkCode):
	"""คืนตัวอักษรของปุ่มที่กดตามแป้นพิมพ์ที่ใช้อยู่ขณะนี้ (เช่น ปุ่ม S บนแป้นไทย = "ห")
	ใช้เป็นทางสำรองในกรณีที่ wx ไม่ได้ส่งค่า Unicode ของปุ่มมาให้ขณะกด Alt
	คืน None ถ้าหาไม่ได้ (เช่น ไม่ได้รันบน Windows)
	"""
	try:
		import ctypes
		user32 = ctypes.windll.user32
		layout = user32.GetKeyboardLayout(0)
		value = user32.MapVirtualKeyExW(vkCode, MAPVK_VK_TO_CHAR, layout) & 0xFFFF
		if value:
			return chr(value)
	except Exception:
		pass
	return None


class RotorDialog(wx.Dialog):
	"""กล่องโต้ตอบเว็บโรเตอร์
	เปิดขึ้นมาโฟกัสจะอยู่ที่รายการของหมวดหมู่แรกทันที
	พิมพ์ตัวอักษร (ในรายการ): กระโดดไปยังรายการถัดไปที่ขึ้นต้นด้วยตัวอักษรนั้น (กดซ้ำเพื่อวนต่อ)
	ลูกศรซ้าย/ขวา (ในรายการ): เปลี่ยนหมวดหมู่ วนไปตามลำดับที่ตั้งค่าไว้
	Shift+Tab (จากรายการ): ไปยังแท็บหมวดหมู่ ใช้ลูกศรซ้าย/ขวาเลือกแท็บ แล้ว Tab กลับเข้ารายการ
	Alt+ตัวอักษร: กระโดดไปยังหมวดหมู่นั้นทันที รองรับทั้งแป้นอังกฤษและแป้นไทยเสมอ
	ลูกศรขึ้น/ลง: เลื่อนดูรายการภายในหมวดหมู่ปัจจุบัน
	Enter/Space: กระโดดไปยังตำแหน่งที่เลือกในเอกสาร แล้วปิดกล่องโต้ตอบ
	Escape: ปิดกล่องโต้ตอบโดยไม่ทำอะไร
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
		self._itemsCache = {}  # itemType -> รายการ QuickNavItem ทั้งหมดที่ดึงมาแล้ว
		self._pages = []  # ข้อมูลของแต่ละแท็บ ตามลำดับเดียวกับ self.categories
		self._gestureBlockActive = False
		self._typeAheadBuffer = ""
		self._typeAheadTime = 0.0

		# ตารางคีย์ลัด Alt+ตัวอักษร -> ลำดับหมวดหมู่ (เฉพาะหมวดที่เปิดใช้งานอยู่จริงในโรเตอร์นี้)
		# ใช้ได้ทั้งตัวอักษรอังกฤษและไทยเสมอ ไม่ขึ้นกับภาษาที่ตั้งค่าไว้ และไม่ขึ้นกับแป้นพิมพ์ที่ใช้อยู่
		self._englishShortcutMap = {}
		self._thaiShortcutMap = {}
		for idx, (_label, itemType) in enumerate(self.categories):
			letter = strings.CATEGORY_SHORTCUTS["en"].get(itemType)
			if letter:
				self._englishShortcutMap[letter.upper()] = idx
			letter = strings.CATEGORY_SHORTCUTS["th"].get(itemType)
			if letter:
				self._thaiShortcutMap[letter] = idx

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

		self._ensurePageLoaded(self.categoryIndex)
		# ย้ายโฟกัสเข้ารายการหลังจากหน้าต่างแสดงขึ้นแล้ว (Show() อาจย้ายโฟกัสไปที่แท็บก่อน)
		wx.CallAfter(self._focusCurrentList)

	def _buildUI(self):
		mainSizer = wx.BoxSizer(wx.VERTICAL)

		self.notebook = wx.Notebook(self)
		for label, _itemType in self.categories:
			panel = wx.Panel(self.notebook)
			pageSizer = wx.BoxSizer(wx.VERTICAL)
			# ข้อความนี้อยู่ก่อนรายการ NVDA จึงอ่านเป็นชื่อของรายการ (เช่น "หัวเรื่อง — 12 รายการ")
			header = wx.StaticText(panel, label=label)
			pageSizer.Add(header, 0, wx.ALL | wx.EXPAND, 6)
			listBox = wx.ListBox(panel, style=wx.LB_SINGLE)
			listBox.SetMinSize((480, 320))
			pageSizer.Add(listBox, 1, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.EXPAND, 6)
			panel.SetSizer(pageSizer)
			self.notebook.AddPage(panel, label)

			listBox.Bind(wx.EVT_KEY_DOWN, self._onListKeyDown)
			listBox.Bind(wx.EVT_CHAR, self._onListChar)
			listBox.Bind(wx.EVT_LISTBOX_DCLICK, self._onActivate)
			self._pages.append({
				"header": header,
				"listBox": listBox,
				"items": [],
				"labels": [],
				"loaded": False,
			})
		mainSizer.Add(self.notebook, 1, wx.ALL | wx.EXPAND, 8)

		hint = wx.StaticText(self, label=(
			strings.tr("rotorHint")
			+ (strings.tr("rotorHintBlockNotice") if cat.getBlockOtherGestures() else "")
		))
		mainSizer.Add(hint, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

		self.SetSizerAndFit(mainSizer)
		self.CentreOnScreen()

		self.notebook.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self._onPageChanged)
		self.Bind(wx.EVT_CHAR_HOOK, self._onCharHook)

	def _onCharHook(self, evt):
		# ใช้ CHAR_HOOK เพื่อดักคีย์สำคัญได้แน่นอนไม่ว่าโฟกัสจะอยู่ที่แท็บหรือรายการ
		code = evt.GetKeyCode()

		if code == wx.WXK_ESCAPE:
			self.Close()
			return

		# Enter: กระโดดไปยังรายการที่เลือกอยู่ในหมวดปัจจุบันเสมอ ไม่ว่าโฟกัสจะอยู่ที่แท็บหรือรายการ
		if code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER) and not evt.AltDown():
			self._onActivate(evt)
			return

		if evt.AltDown() and not evt.ControlDown():
			idx = self._categoryIndexFromAltKey(evt)
			if idx is not None:
				self._switchToCategoryIndex(idx)
				return

		evt.Skip()

	def _categoryIndexFromAltKey(self, evt):
		"""หาว่า Alt+ปุ่มที่กดตรงกับหมวดหมู่ใด
		1) ถ้าปุ่มนั้นให้ตัวอักษรไทยที่อยู่ในตารางคีย์ลัดไทย (แป้นพิมพ์เป็นภาษาไทย) ใช้หมวดตามตารางไทย
		2) ไม่เช่นนั้นใช้ตัวอักษรอังกฤษบนปุ่มนั้น (รหัสปุ่ม A-Z ไม่ขึ้นกับแป้นพิมพ์ที่ใช้อยู่)
		"""
		candidates = []
		uni = evt.GetUnicodeKey()
		if uni and uni != wx.WXK_NONE:
			candidates.append(chr(uni))
		layoutChar = _layoutCharForKey(evt.GetRawKeyCode())
		if layoutChar:
			candidates.append(layoutChar)
		for ch in candidates:
			idx = self._thaiShortcutMap.get(ch)
			if idx is not None:
				return idx

		code = evt.GetKeyCode()
		if ord("A") <= code <= ord("Z"):
			return self._englishShortcutMap.get(chr(code))
		if ord("a") <= code <= ord("z"):
			return self._englishShortcutMap.get(chr(code).upper())
		return None

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
		การนำทางภายในโรเตอร์เอง (ลูกศร, Enter, Esc, การพิมพ์ค้นหา) ใช้กลไกของ wx โดยตรง
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

	def _onListKeyDown(self, evt):
		code = evt.GetKeyCode()
		if evt.AltDown():
			evt.Skip()
		elif code == wx.WXK_LEFT:
			self._switchCategory(-1)
		elif code == wx.WXK_RIGHT:
			self._switchCategory(1)
		elif code in (wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_SPACE):
			self._onActivate(evt)
		else:
			# ปล่อยให้ ListBox จัดการปุ่มขึ้น/ลง/Home/End/Page Up/Page Down และ Tab/Shift+Tab ตามปกติ
			evt.Skip()

	def _onListChar(self, evt):
		"""พิมพ์ตัวอักษรในรายการ: กระโดดไปยังรายการที่ขึ้นต้นด้วยตัวอักษรนั้น
		รองรับทั้งตัวอักษรไทยและอังกฤษ ตามแป้นพิมพ์ที่ใช้อยู่ขณะนั้น
		"""
		if evt.AltDown() or evt.ControlDown():
			evt.Skip()
			return
		uni = evt.GetUnicodeKey()
		if not uni or uni == wx.WXK_NONE or uni < 32 or chr(uni).isspace():
			evt.Skip()
			return
		self._typeAhead(chr(uni))

	def _typeAhead(self, ch):
		page = self._pages[self.categoryIndex]
		labels = page["labels"]
		listBox = page["listBox"]
		if not labels:
			tones.beep(220, 40)
			return

		now = time.monotonic()
		if now - self._typeAheadTime > TYPE_AHEAD_TIMEOUT:
			self._typeAheadBuffer = ""
		self._typeAheadTime = now
		self._typeAheadBuffer += ch.casefold()
		buf = self._typeAheadBuffer

		current = listBox.GetSelection()
		if current == wx.NOT_FOUND:
			current = -1
		count = len(labels)
		if len(set(buf)) == 1:
			# กดตัวอักษรเดิมซ้ำ: วนไปยังรายการถัดไปที่ขึ้นต้นด้วยตัวอักษรนั้น
			prefix = buf[0]
			start = current + 1
		else:
			# พิมพ์หลายตัวต่อกัน: หาคำที่ขึ้นต้นตรงกัน เริ่มจากรายการปัจจุบัน
			prefix = buf
			start = max(current, 0)
		for offset in range(count):
			idx = (start + offset) % count
			if labels[idx].lstrip().casefold().startswith(prefix):
				listBox.SetSelection(idx)
				return
		tones.beep(220, 40)

	def _onPageChanged(self, evt):
		# ผู้ใช้เลือกแท็บด้วยลูกศรซ้าย/ขวา หรือ Ctrl+Tab ขณะโฟกัสอยู่ที่แท็บ
		index = evt.GetSelection()
		if 0 <= index < len(self.categories):
			self.categoryIndex = index
			self._ensurePageLoaded(index)
			log.info("WebRotor: เลือกแท็บหมวดหมู่ '%s'" % self.categories[index][1])
		evt.Skip()

	def _switchCategory(self, step):
		if not self.categories:
			return
		newIndex = (self.categoryIndex + step) % len(self.categories)
		self._switchToCategoryIndex(newIndex)

	def _switchToCategoryIndex(self, index):
		"""เปลี่ยนไปยังหมวดหมู่ที่ระบุ แล้วย้ายโฟกัสไปที่รายการของหมวดนั้น
		NVDA จะอ่านชื่อหมวดหมู่พร้อมจำนวนรายการ (จากหัวข้อเหนือรายการ) และรายการที่เลือกอยู่
		"""
		if not self.categories:
			return
		listBox = self._pages[index]["listBox"]
		if index == self.categoryIndex and self.FindFocus() is listBox:
			# อยู่ที่หมวดนี้แล้ว (เช่น กดคีย์ลัดซ้ำของหมวดเดิม) แค่บอกซ้ำว่าอยู่หมวดไหน
			ui.message(self._pages[index]["header"].GetLabel())
			return
		self.categoryIndex = index
		self._typeAheadBuffer = ""
		self._ensurePageLoaded(index)
		if self.notebook.GetSelection() != index:
			# ChangeSelection ไม่ยิง EVT_NOTEBOOK_PAGE_CHANGED จึงไม่เกิดการทำงานซ้ำ
			self.notebook.ChangeSelection(index)
		log.info("WebRotor: สลับไปหมวดหมู่ '%s'" % self.categories[index][1])
		listBox.SetFocus()

	def _focusCurrentList(self):
		if self._closeHandled or not self._pages:
			return
		self._pages[self.categoryIndex]["listBox"].SetFocus()

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

	def _ensurePageLoaded(self, index):
		"""ดึงรายการของหมวดหมู่นี้ (ครั้งแรกที่เปิดแท็บนี้เท่านั้น) แล้วใส่ลงในรายการของแท็บ"""
		page = self._pages[index]
		if page["loaded"]:
			return
		label, itemType = self.categories[index]
		items = self._ensureItemsLoaded(itemType)

		labels = []
		for it in items:
			text = (it.label or "").strip()
			if not text:
				text = strings.tr("noLabel")
			if len(text) > MAX_LABEL_LENGTH:
				text = text[:MAX_LABEL_LENGTH] + "…"
			labels.append(text)

		listBox = page["listBox"]
		listBox.Freeze()
		listBox.Clear()
		if labels:
			listBox.InsertItems(labels, 0)
			listBox.SetSelection(0)
		listBox.Thaw()

		if labels:
			page["header"].SetLabel(strings.tr("categoryLabelPlain", category=label, total=len(labels)))
		else:
			page["header"].SetLabel(strings.tr("categoryLabelEmpty", category=label))
		page["items"] = items
		page["labels"] = labels
		page["loaded"] = True

	def _onActivate(self, evt):
		if not self._pages:
			return
		page = self._pages[self.categoryIndex]
		sel = page["listBox"].GetSelection()
		if sel == wx.NOT_FOUND or sel >= len(page["items"]):
			return
		item = page["items"][sel]
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
