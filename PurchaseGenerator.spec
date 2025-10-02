# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# ДОБАВЬТЕ ЭТОТ ФАЙЛ В .gitignore ЧТОБЫ ОН НЕ УДАЛЯЛСЯ

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data', 'data'),
        ('ui', 'ui'),
        ('requirements.txt', '.')
    ],
    hiddenimports=[
        'tkinter',
        'customtkinter',
        'openpyxl',
        'pandas',
        'PIL',
        'requests',
        'threading',
        'tempfile',
        'subprocess',
        'pathlib'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Добавляем дополнительные файлы
added_files = []

# Добавляем иконку если есть
icon_path = None
try:
    if os.path.exists('icon.ico'):
        icon_path = 'icon.ico'
        added_files.append(('icon.ico', '.', 'DATA'))
except:
    pass

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    added_files,
    name='PurchaseGenerator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Измените на True для отладки
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)