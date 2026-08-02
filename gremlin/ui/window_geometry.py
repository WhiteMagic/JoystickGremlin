# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from PySide6 import QtCore, QtGui

from gremlin.config import Configuration
from gremlin.types import PropertyType


class WindowGeometry(QtCore.QObject):
    """Loads, validates, and persists a single window's [x, y, w, h].

    Falls back to a screen-centered default (built from the caller-supplied
    default width/height) whenever nothing valid was ever saved, so QML can
    bind x/y/width/height declaratively without a fallback expression.
    """

    def __init__(
        self,
        config: Configuration,
        name: str,
        default_width: int,
        default_height: int,
        min_width: int,
        min_height: int,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._name = name

        if not self._config.exists("global", "general", name):
            self._config.register(
                "global",
                "general",
                name,
                PropertyType.List,
                [],
                f"Persisted window geometry for {name}.",
                {},
                False,
            )

        value = self._config.value("global", "general", name)
        if self._is_valid(value, min_width, min_height):
            self._x, self._y, self._width, self._height = value
        else:
            self._width = default_width
            self._height = default_height
            self._x, self._y = self._centered_position(default_width, default_height)

    @staticmethod
    def _is_valid(value: object, min_width: int, min_height: int) -> bool:
        if not isinstance(value, list) or len(value) != 4:
            return False
        x, y, w, h = value
        if not all(isinstance(v, int) for v in (x, y, w, h)):
            return False
        if w < min_width or h < min_height:
            return False

        # Off-screen if it doesn't intersect any currently attached screen's
        # geometry (e.g. saved on a monitor that's since been unplugged).
        margin = 100
        for screen in QtGui.QGuiApplication.screens():
            geo = screen.geometry()
            if (
                x + w > geo.x() - margin
                and x < geo.x() + geo.width() + margin
                and y + h > geo.y() - margin
                and y < geo.y() + geo.height() + margin
            ):
                return True
        return False

    @staticmethod
    def _centered_position(width: int, height: int) -> tuple[int, int]:
        screen = QtGui.QGuiApplication.primaryScreen()
        if screen is None:
            return 0, 0
        geo = screen.availableGeometry()
        return (
            geo.x() + (geo.width() - width) // 2,
            geo.y() + (geo.height() - height) // 2,
        )

    @QtCore.Property(int, constant=True)
    def x(self) -> int:
        return self._x

    @QtCore.Property(int, constant=True)
    def y(self) -> int:
        return self._y

    @QtCore.Property(int, constant=True)
    def width(self) -> int:
        return self._width

    @QtCore.Property(int, constant=True)
    def height(self) -> int:
        return self._height

    @QtCore.Slot(int, int, int, int)
    def save(self, x: int, y: int, w: int, h: int) -> None:
        self._config.set("global", "general", self._name, [x, y, w, h])
