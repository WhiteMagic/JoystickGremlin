# -*- mode: python -*-

block_cipher = None

added_files = [
    ("doc/getting_started.html", "doc"),
    ("gfx", "gfx"),
    ("templates", "templates"),
]
added_binaries = [
    ("vjoy/vJoyInterface.dll", "."),
    ("SDL2.dll", "."),
]

a = Analysis(
    ["joystick_gremlin.py"],
    pathex=["C:\\Users\\Ivan\\PycharmProjects\\JoystickGremlin"],
    binaries=added_binaries,
    datas=added_files,
    hiddenimports=[],
    hookspath=None,
    runtime_hooks=None,
    excludes=None,
    win_no_prefer_redirects=None,
    win_private_assemblies=None,
    cipher=block_cipher
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=False,
    name="joystick_gremlin",
    debug=False,
    strip=None,
    upx=True,
    console=True,
    icon="gfx\\icon.ico"
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=None,
    upx=True,
    name="joystick_gremlin"
)
