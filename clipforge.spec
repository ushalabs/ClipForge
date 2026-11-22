# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for building ClipForge as a standalone desktop application."""
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [("web", "web"), ("studio/fonts", "studio/fonts")]
binaries = []
hiddenimports = []

for pkg in ("sherpa_onnx", "soundfile", "yt_dlp", "uvicorn", "fastapi", "starlette", "sqlalchemy", "httpx", "webview", "pystray", "PIL"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception:
        hiddenimports += collect_submodules(pkg)

for extra in ("studio.server", "studio.desktop", "psycopg"):
    try:
        hiddenimports += collect_submodules(extra)
    except Exception:
        hiddenimports.append(extra)

icon_path = "build/clipforge.ico" if os.path.exists("build/clipforge.ico") else None

a = Analysis(
    ["desktop.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=list(dict.fromkeys(hiddenimports)),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ClipForge",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="ClipForge",
)
