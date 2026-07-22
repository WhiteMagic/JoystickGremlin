# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Launches the Kobold style playground (guide §6 Phase 3).

Run with `poetry run python scripts/gallery.py`. Unlike the Phase 1/2
throwaway checks, this is permanent: it stays in the repo as the reference
and visual-check surface for every later phase. Press L/D for the shipped
schemes; use the in-window toolbar to switch theme/zoom.

This constructs the real Configuration() singleton and registers config
options exactly like a normal app run, so it does read/write your real
Joystick Gremlin user profile -- run it deliberately, not from automation.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6 import (
    QtCore,
    QtGui,
    QtQml,
)
from PySide6.QtQuickControls2 import QQuickStyle

import gremlin.ui.icon_provider
import gremlin.ui.theme_manager
import gremlin.util
import joystick_gremlin  # noqa: F401 -- side effect: sets up userprofile path


def main() -> int:
    joystick_gremlin.register_config_options()

    QQuickStyle.setStyle("Kobold")
    QQuickStyle.setFallbackStyle("Basic")

    app = QtGui.QGuiApplication(sys.argv)
    gremlin.ui.theme_manager.load_fonts()

    engine = QtQml.QQmlApplicationEngine()
    engine.addImportPath(gremlin.util.resource_path("style/qml"))
    engine.addImageProvider("icon", gremlin.ui.icon_provider.IconProvider())

    manager = gremlin.ui.theme_manager.ThemeManager()
    engine.rootContext().setContextProperty("themeManager", manager)

    engine.load(
        QtCore.QUrl.fromLocalFile(
            str(Path(__file__).parent.parent / "style" / "playground" / "main.qml")
        )
    )
    if not engine.rootObjects():
        return 1

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
