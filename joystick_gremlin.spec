# -*- mode: python ; coding: utf-8 -*-

import os


# Properly enumerate all files required for the action_plugins and
# container_plugins system
action_plugins_files = []
for root, _, files in os.walk("action_plugins"):
    for fname in files:
        if fname.endswith(".pyc"):
            continue
        action_plugins_files.append((os.path.join(root, fname), root))

datas = [
    ("about", "about"),
    ("doc", "doc"),
    ("gfx", "gfx"),
    ("qml", "qml"),
    ("device_db.json", "."),
]
datas.extend(action_plugins_files)
binaries = [
    ("vjoy/vJoyInterface.dll", "."),
    ("dill/dill.dll", "."),
]

hidden_imports = [
    "action_plugins",
    "action_plugins.chain",
    "action_plugins.change_mode",
    "action_plugins.common",
    "action_plugins.condition",
    "action_plugins.condition.comparator",
    "action_plugins.description",
    "action_plugins.double_tap",
    "action_plugins.hat_buttons",
    "action_plugins.load_profile",
    "action_plugins.macro",
    "action_plugins.map_to_io",
    "action_plugins.map_to_keyboard",
    "action_plugins.map_to_mouse",
    "action_plugins.map_to_vjoy",
    "action_plugins.merge_axis",
    "action_plugins.pause_resume",
    "action_plugins.play_sound",
    "action_plugins.reference",
    "action_plugins.response_curve",
    "action_plugins.root",
    "action_plugins.tempo",
    "gremlin.ui",
    "gremlin.ui.action_model",
    "gremlin.ui.backend",
    "gremlin.ui.config",
    "gremlin.ui.device",
    "gremlin.ui.profile",
    "gremlin.ui.util",
]

a = Analysis(
    ['joystick_gremlin.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

# Implementation of a library exclusion system to remove huge and unneded
# Qt libraries
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

pyz = PYZ(a.pure)

single_folder = True

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='joystick_gremlin',
    debug=True,
    bootloader_ignore_signals=False,
    exclude_binaries=single_folder,
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

if single_folder:
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name='joystick_gremlin',
    )
