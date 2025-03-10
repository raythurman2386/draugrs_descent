# -*- mode: python -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['d:\\code\\draugrs_descent'],
    binaries=[],
    datas=[
        # Map source folder to destination folder in the bundle
        ('assets/audio', 'assets/audio'),
        ('assets/audio/scene_audio', 'assets/audio/scene_audio'),
        ('assets/audio/ui_sounds', 'assets/audio/ui_sounds'),
        ('assets/fonts', 'assets/fonts'),
        ('assets/interface', 'assets/interface'),
        ('assets/scribble_dungeons', 'assets/scribble_dungeons'),
        ('assets/maps', 'assets/maps'),
        ('assets/particles', 'assets/particles'),
        ('config/game_config.yaml', 'config'),
        ('data/high_score.json', 'data'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Draugrs Descent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Set to True temporarily for debugging
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Draugrs Descent',
)