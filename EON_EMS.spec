# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['EON_EMS.py'],
    pathex=[],
    binaries=[],
    datas=[
    ('pyqt/icons/*', 'pyqt/icons'),
    ('venv/lib/site-packages/tortoise_orm-0.24.0.dist-info', 'tortoise_orm-0.24.0.dist-info')],
    hiddenimports=['tortoise.backends.sqlite', 'serial'],
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
    a.binaries,
    a.datas,
    [],
    name='EON_EMS',
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
    icon=['pyqt\\icons\\app-icon.ico'],
)
