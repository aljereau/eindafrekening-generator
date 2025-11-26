# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['generate.py'],
    pathex=[],
    binaries=[],
    datas=[('input_template.xlsx', '.'), ('template_onepager.html', '.'), ('template_detail.html', '.'), ('assets', 'assets'), ('migrations', 'migrations'), ('database', 'database')],
    hiddenimports=['openpyxl', 'jinja2', 'weasyprint'],
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
    name='RyanRent_Generator',
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
)
app = BUNDLE(
    exe,
    name='RyanRent_Generator.app',
    icon=None,
    bundle_identifier=None,
)
