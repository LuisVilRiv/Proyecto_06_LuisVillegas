# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('assets', 'assets')]
binaries = []
hiddenimports = ['peewee', 'bcrypt', 'bcrypt._bcrypt', 'sqlite3', 'logging.handlers', 'gui.dialogs.crisis_dialog', 'PySide6.QtSvg', 'PySide6.QtXml', 'PySide6.QtPrintSupport', 'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui']
hiddenimports += collect_submodules('core')
hiddenimports += collect_submodules('domain')
hiddenimports += collect_submodules('models')
hiddenimports += collect_submodules('gui')
tmp_ret = collect_all('peewee')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('PySide6')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'pytest_qt', 'matplotlib', 'numpy', 'reportlab', 'flet', 'pygame'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ScienceWorldPark',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ScienceWorldPark',
)
