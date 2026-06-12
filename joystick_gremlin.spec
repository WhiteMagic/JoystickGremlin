# -*- mode: python ; coding: utf-8 -*-

import os

# Properly enumerate all files required for the action_plugins and
# container_plugins system.
action_plugins_files = []
for root, _, files in os.walk("action_plugins"):
    for fname in files:
        if fname.endswith(".pyc"):
            continue
        action_plugins_files.append((os.path.join(root, fname), root))

datas = [
    ("gfx", "gfx"),
    ("qml", "qml"),
    ("theme", "theme"),
    ("device_db.json", "."),
    ("version.json", ".")
]
datas.extend(action_plugins_files)
binaries = [
    ("vjoy/vJoyInterface.dll", "."),
    ("dill/dill.dll", "."),
]

# List all action plugin code files by their import name as pyinstaller
# doesn't pick them all up automatically.
hidden_imports = [
    "action_plugins",
    "action_plugins.chain",
    "action_plugins.change_mode",
    "action_plugins.common",
    "action_plugins.condition",
    "action_plugins.condition.comparator",
    "action_plugins.condition.condition",
    "action_plugins.description",
    "action_plugins.double_tap",
    "action_plugins.dual_axis_deadzone",
    "action_plugins.hat_buttons",
    "action_plugins.load_profile",
    "action_plugins.macro",
    "action_plugins.map_to_keyboard",
    "action_plugins.map_to_logical_device",
    "action_plugins.map_to_mouse",
    "action_plugins.map_to_vjoy",
    "action_plugins.merge_axis",
    "action_plugins.pause_resume",
    "action_plugins.play_sound",
    "action_plugins.reference",
    "action_plugins.response_curve",
    "action_plugins.root",
    "action_plugins.smart_toggle",
    "action_plugins.split_axis",
    "action_plugins.tempo",
    "action_plugins.text_to_speech",
    "gremlin.ui",
    "gremlin.ui.action_model",
    "gremlin.ui.backend",
    "gremlin.ui.device",
    "gremlin.ui.option",
    "gremlin.ui.profile_devices_model",
    "gremlin.ui.profile",
    "gremlin.ui.script",
    "gremlin.ui.tools",
    "gremlin.ui.type_aliases",
    "gremlin.ui.util",
    "miniaudio",
    "_cffi_backend",
]

exclude_imports = [
    "pythonwin",
    "pywin",
    "pywin.debugger",
    "pywin.debugger.dbgcon",
    "pywin.dialogs",
]

a = Analysis(
    ["joystick_gremlin.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    excludes=exclude_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    noarchive=False,
    optimize=0,
)

# Implementation of a library exclusion system to remove huge and unneded
# Qt libraries.
to_keep = []
to_exclude = [
    "opengl32sw.dll",
    "Qt6DataVisualization.dll",
    "Qt6DataVisualizationQml.dll",
    "Qt6Graphs.dll",
    "Qt6Location.dll",
    "Qt6Pdf.dll",
    "Qt6PdfQuick.dll",
    "Qt6Positioning.dll",
    "Qt6PositioningQuick.dll",
    "Qt6Quick3D.dll",
    "Qt6Quick3DAssetImport.dll",
    "Qt6Quick3DAssetUtils.dll",
    "Qt6Quick3DEffects.dll",
    "Qt6Quick3DHelpers.dll",
    "Qt6Quick3DHelpersImpl.dll",
    "Qt6Quick3DParticleEffects.dll",
    "Qt6Quick3DParticles.dll",
    "Qt6Quick3DRuntimeRender.dll",
    "Qt6Quick3DSpatialAudio.dll",
    "Qt6Quick3DUtils.dll",
    "Qt6Quick3DXr.dll",
    "Qt6QuickControls2FluentWinUI3StyleImpl.dll",
    "Qt6QuickControls2Fusion.dll",
    "Qt6QuickControls2FusionStyleImpl.dll",
    "Qt6QuickControls2Imagine.dll",
    "Qt6QuickControls2ImagineStyleImpl.dll",
    "Qt6QuickControls2Material.dll",
    "Qt6QuickControls2MaterialStyleImpl.dll",
    "Qt6QuickControls2WindowsStyleImpl.dll",
    "Qt6QuickTimeline.dll",
    "Qt6QuickTimelineBlendTrees.dll",
    "Qt6QuickVectorImage.dll",
    "Qt6QuickVectorImageGenerator.dll",
    "Qt6RemoteObjects.dll",
    "Qt6RemoteObjectsQml.dll",
    "Qt6Scxml.dll",
    "Qt6ScxmlQml.dll",
    "Qt6Sensors.dll",
    "Qt6SensorsQuick.dll",
    "Qt6ShaderTools.dll",
    "Qt6SpatialAudio.dll",
    "Qt6Sql.dll",
    "Qt6WebChannel.dll",
    "Qt6WebChannelQuick.dll",
    "Qt6WebEngineCore.dll",
    "Qt6WebEngineQuick.dll",
    "Qt6WebEngineQuickDelegatesQml.dll",
    "Qt6WebSockets.dll",
    "Qt6WebView.dll",
    "Qt6WebViewQuick.dll",
    "Qt63DAnimation.dll",
    "Qt63DCore.dll",
    "Qt63DExtras.dll",
    "Qt63DInput.dll",
    "Qt63DLogic.dll",
    "Qt63DQuick.dll",
    "Qt63DQuickAnimation.dll",
    "Qt63DQuickExtras.dll",
    "Qt63DQuickInput.dll",
    "Qt63DQuickLogic.dll",
    "Qt63DQuickRender.dll",
    "Qt63DQuickScene2D.dll",
    "Qt63DQuickScene3D.dll",
    "Qt63DRender.dll",
]
directory_excludes = [
    "Pythonwin",
    "PySide6\\translations",
]

# Only keep binaries we actually want, exlucindg a bunch of Qt libraries.
for (dest, source, kind) in a.binaries:
    skip_file = False
    # Skip directories we want to exclude entirely.
    for directory in directory_excludes:
        if dest.startswith(directory):
            skip_file = True
    # Only add files not on the exclude list.
    if not skip_file and os.path.split(dest)[1] not in to_exclude:
        to_keep.append((dest, source, kind))
a.binaries = to_keep

datas_to_keep = []
for (dest, source, kind) in a.datas:
    skip_file = False
    # Skip directories we want to exclude entirely.
    for directory in directory_excludes:
        if dest.startswith(directory):
            skip_file = True
    # Only add files not on the exclude list.
    if not skip_file:
        datas_to_keep.append((dest, source, kind))
a.datas = datas_to_keep

pyz = PYZ(a.pure)

single_folder = True

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="joystick_gremlin",
    debug=True,
    bootloader_ignore_signals=False,
    exclude_binaries=single_folder,
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
    icon="gfx\\icon.ico",
)
if single_folder:
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="joystick_gremlin",
    )
