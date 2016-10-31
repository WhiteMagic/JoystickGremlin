# -*- mode: python -*-

import os

block_cipher = None

# Properly enumerate all files required for the action_plugins syustem
action_plugins_files = []
for root, _, files in os.walk("action_plugins"):
    for fname in files:
        if fname.endswith(".pyc"):
            continue
        action_plugins_files.append((os.path.join(root, fname), root))

added_files = [
    ("about", "about"),
    ("doc", "doc"),
    ("gfx", "gfx"),
    ("templates", "templates")
]
added_files.extend(action_plugins_files)
added_binaries = [
    ("vjoy/vJoyInterface.dll", "."),
    ("SDL2.dll", "."),
]

a = Analysis(
    ["joystick_gremlin.py"],
    pathex=['C:\\Users\\Ivan Dolvich\\PycharmProjects\\JoystickGremlin'],
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
    exclude_binaries=True,
    name="joystick_gremlin",
    debug=False,
    strip=None,
    upx=True,
    console=False,
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
