# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for ThingKeeper.

Builds a onedir bundle with all assets.  Used by the release workflow
for both Windows (zip) and Linux (AppImage) distributions.

Usage:
    pyinstaller thingkeeper.spec --noconfirm --clean
"""

import sys
from pathlib import Path

block_cipher = None

assets = [
    ("thingkeeper/assets/app.ico", "thingkeeper/assets"),
    ("thingkeeper/assets/icon.png", "thingkeeper/assets"),
    ("thingkeeper/assets/icon-256.png", "thingkeeper/assets"),
    ("thingkeeper/assets/icon.svg", "thingkeeper/assets"),
]

datas = [(str(src), str(dst)) for src, dst in assets if Path(src).exists()]

hiddenimports = [
    "cryptography.fernet",
    "reportlab.platypus",
    "reportlab.lib",
    "openpyxl",
    "PIL",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "numpy", "scipy", "pandas"],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ThingKeeper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon="thingkeeper/assets/app.ico" if sys.platform == "win32" else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="ThingKeeper",
)
