# -*- coding: utf-8 -*-
"""สร้างไฟล์ติดตั้ง .nvda-addon จากโฟลเดอร์ addon/

วิธีใช้:  python build.py
ผลลัพธ์:  dist/webRotor-<version>.nvda-addon  (อ่าน name/version จาก addon/manifest.ini)
"""

import pathlib
import re
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "addon"
DIST = ROOT / "dist"
SKIP_DIRS = {"__pycache__"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def readManifestField(field):
	text = (SRC / "manifest.ini").read_text(encoding="utf-8")
	match = re.search(r"^%s\s*=\s*(.+)$" % field, text, re.MULTILINE)
	if not match:
		raise SystemExit("ไม่พบ %s ใน addon/manifest.ini" % field)
	return match.group(1).strip()


def main():
	name = readManifestField("name")
	version = readManifestField("version")
	DIST.mkdir(exist_ok=True)
	out = DIST / ("%s-%s.nvda-addon" % (name, version))
	with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
		for path in sorted(SRC.rglob("*")):
			if path.is_dir() or path.suffix in SKIP_SUFFIXES:
				continue
			if any(part in SKIP_DIRS for part in path.parts):
				continue
			zf.write(path, path.relative_to(SRC).as_posix())
	print("สร้างไฟล์แล้ว: %s" % out.relative_to(ROOT))


if __name__ == "__main__":
	main()
