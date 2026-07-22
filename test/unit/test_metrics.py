# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Metrics-resolution test (guide §7): every Metrics token must resolve to
a whole pixel at each supported UI scale. Tokens are discovered via
QMetaObject introspection rather than a hardcoded list, so this keeps
catching regressions as later phases add more Metrics tokens.
"""

from __future__ import annotations

import pathlib

from PySide6 import (
    QtCore,
    QtGui,
    QtQml,
)

import gremlin.ui.theme_manager as theme_manager

_STYLE_QML_DIR = pathlib.Path(__file__).parents[2] / "style" / "qml"

# Not dimension tokens: the scale ratio itself is non-integer by design
# (e.g. 1.5), and scalePercentage/objectName aren't sized in pixels.
_EXCLUDED_PROPERTIES = {"scale", "scalePercentage", "objectName"}
_NUMERIC_TYPES = {"int", "double", "qreal", "float"}


def _load_metrics() -> tuple[theme_manager.ThemeManager, QtCore.QObject]:
    """Loads the Metrics singleton behind a live-bound ThemeManager.

    Returns:
        The ThemeManager (to drive scale changes) and the Metrics QObject.
    """
    QtGui.QGuiApplication.instance() or QtGui.QGuiApplication([])

    manager = theme_manager.ThemeManager()
    engine = QtQml.QQmlApplicationEngine()
    engine.rootContext().setContextProperty("themeManager", manager)
    engine.addImportPath(str(_STYLE_QML_DIR))
    engine.loadData(
        b"import QtQuick\n"
        b"import Kobold.Foundation\n"
        b"QtObject { property QtObject metricsRef: Metrics }\n",
        QtCore.QUrl("inline.qml"),
    )
    assert len(engine.rootObjects()) == 1
    root = engine.rootObjects()[0]
    metrics = root.property("metricsRef")
    assert metrics is not None
    # Keep the engine alive for the caller's lifetime by stashing it on the
    # object the caller already holds -- letting it be GC'd tears down the
    # QML context the returned Metrics instance depends on.
    metrics._engine_keepalive = engine  # noqa: SLF001
    return manager, metrics


def _numeric_token_names(metrics: QtCore.QObject) -> list[str]:
    """Returns the names of Metrics' numeric, non-excluded properties."""
    meta = metrics.metaObject()
    names = []
    for index in range(meta.propertyCount()):
        prop = meta.property(index)
        name = prop.name()
        if name in _EXCLUDED_PROPERTIES:
            continue
        if prop.typeName() in _NUMERIC_TYPES:
            names.append(name)
    return names


def test_every_metrics_token_resolves_to_a_whole_pixel_at_every_scale() -> None:
    manager, metrics = _load_metrics()

    token_names = _numeric_token_names(metrics)
    assert token_names, "expected Metrics.qml to expose numeric dimension tokens"

    for scale in ("100", "150", "200"):
        manager.set_ui_scale(scale)
        for name in token_names:
            value = metrics.property(name)
            assert value == round(value), (
                f"Metrics.{name} resolved to {value} at {scale}% scale, "
                "which is not a whole pixel"
            )


def test_the_whole_pixel_assertion_catches_a_fractional_token() -> None:
    # Proves the check above actually has teeth: a token that skips dp()'s
    # rounding (e.g. `x * scale` instead of `Math.round(x * scale)`) lands
    # on a fractional value at 150% and must fail the same assertion.
    QtGui.QGuiApplication.instance() or QtGui.QGuiApplication([])
    engine = QtQml.QQmlApplicationEngine()
    engine.loadData(
        b"import QtQuick\nQtObject { property real unrounded: 13 * 1.5 }\n",
        QtCore.QUrl("unrounded.qml"),
    )
    root = engine.rootObjects()[0]
    value = root.property("unrounded")

    assert value != round(value)
