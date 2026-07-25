# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import collections
import threading

from PySide6 import (
    QtCore,
    QtGui,
    QtQuick,
    QtSvg,
)


class _BaseIconProvider(QtQuick.QQuickImageProvider):
    """Shared `image://<provider>/<id>?c=<hex>&px=<size>` pipeline.

    Handles caching, id parsing, `currentColor` substitution and rasterization.
    Subclasses only decide how `<id>` (the part before `?`) maps to a QFile.
    """

    def __init__(self, max_cache_size: int = 200) -> None:
        """Initialize the image provider.

        Args:
            max_cache_size: Maximum number of rendered images to cache.
                When the limit is reached, the oldest entry is evicted.
        """
        super().__init__(QtQuick.QQuickImageProvider.ImageType.Image)
        self._cache: collections.OrderedDict[str, QtGui.QImage] = (
            collections.OrderedDict()
        )
        self._max_cache_size = max_cache_size
        self._lock = threading.Lock()

    def requestImage(
        self, image_id: str, size: QtCore.QSize, requested_size: QtCore.QSize
    ) -> QtGui.QImage:
        """Returns the recolored icon image for the given id, rendering it if needed.

        Args:
            image_id: The "<name>?c=<hex>&px=<size>" part of the image URI
                image://<provider>/<image id>
            size: Output parameter for the actual image size (not used)
            requested_size: The size requested by QML (not used)

        Returns:
            A QImage of the requested icon with the requested size and color.
        """
        with self._lock:
            if image_id in self._cache:
                self._cache.move_to_end(image_id)
                return self._cache[image_id]

        name, color, px = self._parse_image_id(image_id)
        image = self._render(name, color, px)

        with self._lock:
            if len(self._cache) >= self._max_cache_size:
                self._cache.popitem(last=False)
            self._cache[image_id] = image
            return image

    def _parse_image_id(self, image_id: str) -> tuple[str, str, int]:
        """Splits an image id into its icon name, hex color, and pixel size.

        Args:
            image_id: The "<name>?c=<hex>&px=<size>" image id, as passed to
                requestImage

        Returns:
            Tuple (name, color, px) tuple, with color defaulting to "000000" and
            "px" to 16, if not specified.
        """
        name, _, query = image_id.partition("?")
        params: dict[str, str] = {}
        for pair in query.split("&"):
            if pair:
                key, _, value = pair.partition("=")
                params[key] = value
        color = params.get("c", "000000")
        px = int(params.get("px", "16"))
        return name, color, px

    def _open(self, name: str) -> QtCore.QFile:
        """Maps an icon id to the QFile it should be read from.

        Args:
            name: The id portion (before "?") of the request.

        Returns:
            A QFile ready to be opened for the icon's SVG source.
        """
        raise NotImplementedError

    def _render(self, name: str, color: str, px: int) -> QtGui.QImage:
        """Loads, recolors, and rasterizes the icon SVG resolved from `name`.

        Args:
            name: The id portion (before "?") of the request, resolved to a
                QFile via `_open`.
            color: Hex color (without "#") to substitute for `currentColor`
            px: Width and height, in pixels, to rasterize at

        Returns:
            A QImage of the recolored icon, or a null QImage if the SVG source
            for `name` could not be opened.
        """
        handle = self._open(name)
        if not handle.open(
            QtCore.QIODevice.OpenModeFlag.ReadOnly | QtCore.QIODevice.OpenModeFlag.Text
        ):
            return QtGui.QImage()
        try:
            svg_data = bytes(handle.readAll().data()).decode("utf-8")
        finally:
            handle.close()

        svg_data = svg_data.replace("currentColor", f"#{color}")

        renderer = QtSvg.QSvgRenderer(svg_data.encode("utf-8"))
        image = QtGui.QImage(px, px, QtGui.QImage.Format.Format_ARGB32_Premultiplied)
        image.fill(QtCore.Qt.GlobalColor.transparent)

        painter = QtGui.QPainter(image)
        try:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            renderer.render(painter)
        finally:
            painter.end()

        return image


class IconProvider(_BaseIconProvider):
    """Rasterizes and recolors the bundled Kobold style icon glyphs on demand.

    Handles `image://icon/<name>?c=<hex>&px=<size>` requests by loading
    `:/style-icons/<name>.svg`.
    """

    def _open(self, name: str) -> QtCore.QFile:
        return QtCore.QFile(f":/style-icons/{name}.svg")


class ActionIconProvider(_BaseIconProvider):
    """Rasterizes and recolors plugin-authored action type icons on demand.

    Handles `image://action-icon/<uri>?c=<hex>&px=<size>` requests, where
    `<uri>` is a `file:///...` URI pointing directly at an `icon.svg` on disk —
    core or user-authored alike, since neither is embedded in the qrc.
    """

    def _open(self, name: str) -> QtCore.QFile:
        return QtCore.QFile(QtCore.QUrl(name).toLocalFile())
