# MorningStarStrategy.spec

block_cipher = None

a = Analysis(
    ['gui_app.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('.env', '.'),
    ],
    hiddenimports=[
        'customtkinter',
        'dhanhq',
        'pyotp',
        'schedule',
        'websocket',
        'websocket._app',
        'websocket._core',
        'pandas',
        'pytz',
        'dotenv',
        'requests',
        'PIL',
        'PIL._tkinter_finder',
        'config',
        'pattern_detector',
        'session_guard',
        'strike_selector',
        'order_manager',
        'trade_tracker',
        'dhan_token_manager',
        'main',
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

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='MorningStarStrategy',
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
