# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_all, copy_metadata

# 1. Base custom files to include in the executable
datas = [
    ('ca_dashboard_app.py', '.'),
    ('database.py', '.'),
    ('utils.py', '.'),
    ('ca_consulting.db', '.'),
]

binaries = []

# 2. Comprehensive hidden imports list to avoid runtime ModuleNotFoundError
hiddenimports = [
    'streamlit',
    'streamlit.web.cli',
    'streamlit.runtime.scriptrunner.magic_funcs',
    'streamlit.runtime.caching',
    'pandas',
    'plotly',
    'plotly.express',
    'plotly.graph_objects',
    'openpyxl',
    'sqlite3',
    'email',
    'email.mime',
    'email.mime.multipart',
    'email.mime.text',
    'email.mime.base',
    'email.mime.application',
    'email.mime.message',
    'email.mime.image',
    'email.mime.audio',
    'email.mime.nonmultipart',
    'smtplib',
]

# 3. Collect assets, binaries, and submodules for heavy packages
packages_to_collect = ['streamlit', 'plotly', 'pandas', 'openpyxl', 'altair']
for pkg in packages_to_collect:
    try:
        tmp_datas, tmp_binaries, tmp_hidden = collect_all(pkg)
        datas += tmp_datas
        binaries += tmp_binaries
        hiddenimports += tmp_hidden
    except Exception as e:
        print(f"Warning collecting {pkg}: {e}")

# 4. Copy package metadata required for runtime version checks
metadata_packages = ['streamlit', 'plotly', 'pandas', 'openpyxl', 'altair']
for meta_pkg in metadata_packages:
    try:
        datas += copy_metadata(meta_pkg)
    except Exception as e:
        print(f"Warning copying metadata for {meta_pkg}: {e}")

a = Analysis(
    ['run_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CA_Dashboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
