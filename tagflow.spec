# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para TagFlow
# Uso: pyinstaller tagflow.spec

import sys
import os

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('version.txt',      '.'),
        ('tagflow_icon.png', '.'),
        ('ui',               'ui'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'send2trash',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Módulos que ya no usamos
        'firebase_admin',
        'google.auth',
        'auth',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TagFlow',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # sin ventana de consola
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Icono según plataforma
    icon='tagflow_icon.png' if sys.platform != 'darwin' else 'tagflow_icon.icns',
)

# macOS: crear .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='TagFlow.app',
        icon='tagflow_icon.icns',
        bundle_identifier='com.tagflow.app',
        info_plist={
            'NSHighResolutionCapable': True,
            'CFBundleShortVersionString': '1.0.0',
            'LSMinimumSystemVersion': '10.15',
        },
    )
