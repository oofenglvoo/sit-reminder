# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置：单文件、无控制台窗口。

用法：pyinstaller --clean --noconfirm build.spec
产物：dist/SitReminder.exe
"""

from PyInstaller.utils.hooks import collect_submodules

hiddenimports = []
hiddenimports += collect_submodules("winrt")
hiddenimports += collect_submodules("windows_toasts")

# 排除体积大且用不到的 Qt 模块，显著减小 exe 体积
excludes = [
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtWebChannel",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtQuick",
    "PySide6.QtQuick3D",
    "PySide6.QtQml",
    "PySide6.Qt3DCore",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtDesigner",
    "PySide6.QtBluetooth",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "tkinter",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("assets", "assets")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SitReminder",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icon.ico",
)
