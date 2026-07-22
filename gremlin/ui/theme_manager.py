# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import json
import logging

import jsonschema
from PySide6 import (
    QtCore,
    QtGui,
)

import gremlin.ui.type_aliases as ta
from gremlin import error
from gremlin.config import Configuration
from gremlin.signal import signal

QML_IMPORT_NAME = "Kobold.Foundation"
QML_IMPORT_MAJOR_VERSION = 1

_TOKENS = (
    "bg",
    "bgAlt",
    "bgHover",
    "bgSelected",
    "line",
    "fg",
    "fgMuted",
    "fgDisabled",
    "accent",
    "error",
    "warning",
)
_DEFAULT_THEME = "light"
_VALID_UI_SCALES = ("100", "150", "200")
_SCHEMA_FILE_NAME = "scheme.schema.json"


def _read_qfile(path: str) -> str:
    """Reads a text file's full content via QFile.

    Args:
        path: Path to the file to read.

    Returns:
        The file's contents as a string.
    """
    # QFile handles both qrc resource paths as well as plain filesystem paths.
    handle = QtCore.QFile(path)
    if not handle.open(
        QtCore.QIODevice.OpenModeFlag.ReadOnly | QtCore.QIODevice.OpenModeFlag.Text
    ):
        raise error.GremlinError(f"Unable to open '{path}'")
    try:
        return bytes(handle.readAll().data()).decode("utf-8")
    finally:
        handle.close()


def load_fonts() -> None:
    """Registers the bundled IBM Plex faces with QFontDatabase.

    Fails loudly (raises) rather than falling back to a system font.
    """
    for path in (
        ":/fonts/IBMPlexSans-Regular.otf",
        ":/fonts/IBMPlexSans-SemiBold.otf",
        ":/fonts/IBMPlexMono-Regular.otf",
        ":/fonts/IBMPlexMono-SemiBold.otf",
    ):
        if QtGui.QFontDatabase.addApplicationFont(path) == -1:
            raise error.GremlinError(f"Failed to load bundled font '{path}'")


class ThemeManager(QtCore.QObject):
    """Owns Kobold color scheme discovery, validation, and the active scheme.

    Exposes the 11 color tokens plus the UI zoom percentage as QML properties.
    """

    changed = QtCore.Signal()

    def __init__(
        self, root_paths: list[str] | None = None, parent: ta.OQO = None
    ) -> None:
        """Discovers themes and activates the configured theme and UI scale.

        Args:
            roots: Directories to search for theme files.
            parent: parent object
        """
        super().__init__(parent)
        self._root_paths = root_paths if root_paths is not None else [":/themes"]
        self._themes: dict[str, dict] = {}
        self._active_colors: dict[str, QtGui.QColor] = {}
        self._active_theme = ""
        self._ui_scale = 100

        self._json_schema = json.loads(
            _read_qfile(f"{self._root_paths[0]}/{_SCHEMA_FILE_NAME}")
        )
        self._discover()
        self._ui_scale = self._get_ui_scale()
        self._apply(self._get_current_theme())

        signal.configChanged.connect(self._config_changed_cb)

    def _discover(self) -> None:
        """Loads and validates every theme JSON file across the roots list."""
        for root in self._root_paths:
            directory = QtCore.QDir(root)
            for file_name in directory.entryList(["*.json"], QtCore.QDir.Filter.Files):
                if file_name == _SCHEMA_FILE_NAME:
                    continue
                self._load_theme_file(directory.filePath(file_name))

    def _load_theme_file(self, path: str) -> None:
        """Loads and schema-validates a single scheme file, rejecting it on failure.

        Args:
            path: Path to the theme file to load and validate.
        """
        theme_name = QtCore.QFileInfo(path).completeBaseName()
        try:
            data = json.loads(_read_qfile(path))
            jsonschema.validate(instance=data, schema=self._json_schema)
        except (error.GremlinError, ValueError, jsonschema.ValidationError) as e:
            logging.getLogger("system").warning(
                f"Rejected Kobold color theme '{path}': {e}"
            )
            return
        self._themes[theme_name] = data

    def _get_current_theme(self) -> str:
        """Returns the name of the currently active theme.

        Returns:
            Name of the currently selected theme, with default fallback.
        """
        theme_name = Configuration().value("global", "general", "theme")
        if theme_name in self._themes:
            return theme_name
        return _DEFAULT_THEME

    def _get_ui_scale(self) -> int:
        """Returns the configured UI scale.

        Returns:
            Current UI scale, defaulting to 100.
        """
        scale = Configuration().value("global", "general", "ui-scale")
        if scale not in _VALID_UI_SCALES:
            return 100
        return int(scale)

    def _apply(self, theme_name: str) -> None:
        """Applies the colors of the provided theme.

        Args:
            theme_name: Name of the theme to apply.
        """
        colors = self._themes[theme_name]["colors"]
        self._active_colors = {token: QtGui.QColor(colors[token]) for token in _TOKENS}
        self._active_theme = theme_name
        self._set_title_bar_appearance(self._themes[theme_name]["meta"]["appearance"])
        self.changed.emit()

    def _set_title_bar_appearance(self, appearance: str | None) -> None:
        """Match the title bar's color to the scheme.

        Args:
            appearance: Appearance of the scheme, either "light" or "dark".
        """
        if appearance not in ("light", "dark"):
            return
        try:
            color_scheme = (
                QtCore.Qt.ColorScheme.Dark
                if appearance == "dark"
                else QtCore.Qt.ColorScheme.Light
            )
            QtGui.QGuiApplication.styleHints().setColorScheme(color_scheme)
        except Exception as e:  # noqa: BLE001
            logging.getLogger("system").warning(
                f"Failed to set title bar color scheme: {e}"
            )

    def _config_changed_cb(self) -> None:
        """Callback handling configuration changes."""
        theme_name = self._get_current_theme()
        ui_scale = self._get_ui_scale()
        if theme_name == self._active_theme and ui_scale == self._ui_scale:
            return
        self._ui_scale = ui_scale
        self._apply(theme_name)

    @QtCore.Slot(str)
    def set_theme(self, theme_name: str) -> None:
        """Sets the given theme, persisting it and updating the UI.

        Args:
            theme_name: Name of the theme to apply.
        """
        if theme_name not in self._themes:
            logging.getLogger("system").warning(f"Unknown theme '{theme_name}'")
            return
        Configuration().set("global", "general", "theme", theme_name)
        signal.configChanged.emit()

    @QtCore.Property(list, constant=True)
    def themeNames(self) -> list[str]:
        return sorted(self._themes.keys())

    @QtCore.Property(int, notify=changed)
    def uiScale(self) -> int:
        return self._ui_scale

    @QtCore.Property(QtGui.QColor, notify=changed)
    def bg(self) -> QtGui.QColor:
        return self._active_colors["bg"]

    @QtCore.Property(QtGui.QColor, notify=changed)
    def bgAlt(self) -> QtGui.QColor:
        return self._active_colors["bgAlt"]

    @QtCore.Property(QtGui.QColor, notify=changed)
    def bgHover(self) -> QtGui.QColor:
        return self._active_colors["bgHover"]

    @QtCore.Property(QtGui.QColor, notify=changed)
    def bgSelected(self) -> QtGui.QColor:
        return self._active_colors["bgSelected"]

    @QtCore.Property(QtGui.QColor, notify=changed)
    def line(self) -> QtGui.QColor:
        return self._active_colors["line"]

    @QtCore.Property(QtGui.QColor, notify=changed)
    def fg(self) -> QtGui.QColor:
        return self._active_colors["fg"]

    @QtCore.Property(QtGui.QColor, notify=changed)
    def fgMuted(self) -> QtGui.QColor:
        return self._active_colors["fgMuted"]

    @QtCore.Property(QtGui.QColor, notify=changed)
    def fgDisabled(self) -> QtGui.QColor:
        return self._active_colors["fgDisabled"]

    @QtCore.Property(QtGui.QColor, notify=changed)
    def accent(self) -> QtGui.QColor:
        return self._active_colors["accent"]

    @QtCore.Property(QtGui.QColor, notify=changed)
    def error(self) -> QtGui.QColor:
        return self._active_colors["error"]

    @QtCore.Property(QtGui.QColor, notify=changed)
    def warning(self) -> QtGui.QColor:
        return self._active_colors["warning"]
