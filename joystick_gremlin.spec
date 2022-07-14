# -*- mode: python -*-

import os

block_cipher = None

# Properly enumerate all files required for the action_plugins and
# container_plugins system
action_plugins_files = []
for root, _, files in os.walk("action_plugins"):
    for fname in files:
        if fname.endswith(".pyc"):
            continue
        action_plugins_files.append((os.path.join(root, fname), root))
container_plugins_files = []

added_files = [
    ("about", "about"),
    ("doc", "doc"),
    ("gfx", "gfx"),
    ("qml", "qml")
]
added_files.extend(action_plugins_files)
added_files.extend(container_plugins_files)
added_binaries = [
    ("vjoy/vJoyInterface.dll", "."),
    ("dill/dill.dll", "."),
]

a = Analysis(
    ["jg_qml.py"],
    pathex=['C:\\Users\\Ivan\\Code\\JoystickGremlin'],
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

to_keep = []
to_exclude = {
    "Qt6WebChannel.dll",
    "Qt6WebEngineCore.dll",
    "Qt6WebEngineQuick.dll",
    "Qt6WebEngineQuickDelegatesQml.dll",
    "Qt6WebSockets.dll"
}
# Only keep binaries we actually want, exlucindg a bunch of Qt crap
for (dest, source, kind) in a.binaries:
    if os.path.split(dest)[1] not in to_exclude:
        to_keep.append((dest, source, kind))
a.binaries = to_keep

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
