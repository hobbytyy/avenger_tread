# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/Users/mac/Documents/QT/Qt_main.py'],
    pathex=[],
    binaries=[],
    datas=[('数据', '数据'), ('策略', '策略'), ('utils', 'utils'), ('界面ui', '界面ui')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'email', 'xml'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='量化回测系统',
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
    name='量化回测系统',
)
app = BUNDLE(
    coll,
    name='量化回测系统.app',
    icon=None,
    bundle_identifier=None,
)
