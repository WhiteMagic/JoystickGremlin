# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json
import pathlib

import jsonschema
import pytest
from PySide6 import (
    QtCore,
    QtGui,
    QtQml,
)

import gremlin.ui.theme_manager as theme_manager

_LIGHT_COLORS = {
    "bg": "#ffffff",
    "bgAlt": "#f2f2f4",
    "bgHover": "#e8e8ec",
    "bgSelected": "#dcdce2",
    "line": "#c4c4cc",
    "fg": "#17171a",
    "fgMuted": "#6a6a74",
    "fgDisabled": "#a6a6b0",
    "accent": "#1060c0",
    "error": "#c0281c",
    "warning": "#9a5c00",
}
_DARK_COLORS = {
    "bg": "#242429",
    "bgAlt": "#1b1b1e",
    "bgHover": "#2e2e34",
    "bgSelected": "#3a3a42",
    "line": "#4a4a54",
    "fg": "#e6e6ea",
    "fgMuted": "#94949e",
    "fgDisabled": "#5c5c66",
    "accent": "#58a6ff",
    "error": "#ff7b6b",
    "warning": "#e0a63c",
}

_THEMES_DIR = pathlib.Path(__file__).parents[2] / "style" / "themes"


def test_shipped_schemes_resolve_expected_colors() -> None:
    manager = theme_manager.ThemeManager()

    manager.set_theme("light")
    for token, hex_value in _LIGHT_COLORS.items():
        assert getattr(manager, token) == QtGui.QColor(hex_value)

    manager.set_theme("dark")
    for token, hex_value in _DARK_COLORS.items():
        assert getattr(manager, token) == QtGui.QColor(hex_value)


def test_discover_theme_names_returns_shipped_schemes() -> None:
    assert theme_manager.discover_theme_names() == ["dark", "light", "zenburn"]


def test_malformed_scheme_rejected(tmp_path: pathlib.Path) -> None:
    valid = {"meta": {"appearance": "light"}, "colors": _LIGHT_COLORS}
    (tmp_path / "valid.json").write_text(json.dumps(valid))

    # Missing the required "accent" key.
    malformed_colors = dict(_LIGHT_COLORS)
    del malformed_colors["accent"]
    malformed = {"meta": {"appearance": "light"}, "colors": malformed_colors}
    (tmp_path / "malformed.json").write_text(json.dumps(malformed))

    manager = theme_manager.ThemeManager(root_paths=[str(_THEMES_DIR), str(tmp_path)])

    assert "malformed" not in manager.themeNames
    assert "valid" in manager.themeNames
    # The manager must still have resolved a usable active scheme.
    assert manager.bg.isValid()


def test_scheme_schema_validates() -> None:
    schema = json.loads((_THEMES_DIR / "scheme.schema.json").read_text())
    for name in ("light.json", "dark.json"):
        data = json.loads((_THEMES_DIR / name).read_text())
        jsonschema.validate(instance=data, schema=schema)


def test_scheme_schema_rejects_planted_bad_schemes() -> None:
    schema = json.loads((_THEMES_DIR / "scheme.schema.json").read_text())
    valid = {"meta": {"appearance": "light"}, "colors": _LIGHT_COLORS}

    missing_key = {"meta": valid["meta"], "colors": dict(_LIGHT_COLORS)}
    del missing_key["colors"]["accent"]

    extra_key = {"meta": valid["meta"], "colors": dict(_LIGHT_COLORS, extra="#000000")}

    alpha_color = {
        "meta": valid["meta"],
        "colors": dict(_LIGHT_COLORS, accent="#1060c0ff"),
    }

    bad_appearance = {"meta": {"appearance": "solarized"}, "colors": _LIGHT_COLORS}

    for bad_scheme in (missing_key, extra_key, alpha_color, bad_appearance):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(instance=bad_scheme, schema=schema)


def test_theme_qml_facade_live_update() -> None:
    # A bare QGuiApplication (not the full JoystickGremlinApp) is all a
    # QQmlApplicationEngine needs; reuse one if pytest-qt already created it.
    QtGui.QGuiApplication.instance() or QtGui.QGuiApplication([])

    manager = theme_manager.ThemeManager()
    manager.set_theme("light")

    engine = QtQml.QQmlApplicationEngine()
    engine.rootContext().setContextProperty("themeManager", manager)
    engine.addImportPath(str(pathlib.Path(__file__).parents[2] / "style" / "qml"))
    engine.loadData(
        b"import QtQuick\n"
        b"import Kobold.Foundation\n"
        b"QtObject { property color c: Theme.bg }\n",
        QtCore.QUrl("inline.qml"),
    )

    assert len(engine.rootObjects()) == 1
    root = engine.rootObjects()[0]
    assert root.property("c") == QtGui.QColor(_LIGHT_COLORS["bg"])

    manager.set_theme("dark")
    assert root.property("c") == QtGui.QColor(_DARK_COLORS["bg"])
