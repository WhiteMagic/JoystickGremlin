# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import collections
import logging
import threading

from PySide6 import (
    QtCore,
    QtGui,
    QtQuick,
)


class ActionSummaryImageProvider(QtQuick.QQuickImageProvider):

    """Generates action sequence visualizations.

    This provider renders visual summary images for input action sequences
    on demand, caches them to avoid redundant rendering, and exposes them
    to QML through the image://action_summary/ URI scheme.
    """

    def __init__(self, max_cache_size: int = 500) -> None:
        """Initialize the image provider.

        Args:
            max_cache_size: Maximum number of rendered images to cache.
                When the limit is reached, the oldest entry is evicted.
        """
        super().__init__(QtQuick.QQuickImageProvider.ImageType.Image)

        self._cache = collections.OrderedDict()
        self._max_cache_size = max_cache_size
        self._lock = threading.Lock()

        # Dimensions controlling layouting.
        self._spacing = 2
        self._glyph_height = 21

        # Set up fonts and metrics for rendering.
        self._bootstrap_font = QtGui.QFont("bootstrap-icons")
        self._bootstrap_font.setPixelSize(15)
        self._bootstrap_metrics = QtGui.QFontMetrics(self._bootstrap_font)

        self._segoe_font = QtGui.QFont("Segoe UI")
        self._segoe_font.setPixelSize(19)
        self._segoe_metrics = QtGui.QFontMetrics(self._segoe_font)

        self._vjoy_font = QtGui.QFont("Segoe UI")
        self._vjoy_font.setPixelSize(11)
        self._vjoy_metrics = QtGui.QFontMetrics(self._vjoy_font)

    def requestImage(
        self,
        image_id: str,
        size: QtCore.QSize,
        requested_size: QtCore.QSize
    ) -> QtGui.QImage:
        """Returns the image for the given id, generating it if needed.

        Args:
            image_id: The action string part of the image URI
                image://action_summary/<image id>
            size: Output parameter for the actual image size (not used)
            requested_size: The size requested by QML (not used)

        Returns:
            A QImage representing the action summary
        """
        with self._lock:
            if image_id in self._cache:
                self._cache.move_to_end(image_id)
                return self._cache[image_id]

        image = self._render(image_id)

        with self._lock:
            if len(self._cache) >= self._max_cache_size:
                self._cache.popitem(last=False)
            self._cache[image_id] = image
            return image

    def _render(self, action_string: str) -> QtGui.QImage:
        """Renders an action sequence image.

        Args:
            action_string: The action sequence string to render

        Returns:
            A QImage containing the rendered action sequence
        """
        tokens = action_string.split(":") if action_string else []

        picture = QtGui.QPicture()
        painter = QtGui.QPainter(picture)

        try:
            painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
            painter.setPen(QtGui.QColor(0, 0, 0))

            x_offset = 0
            for token in tokens:
                if token in ["(", ")"]:
                    painter.setFont(self._segoe_font)
                    glyph_width = self._segoe_metrics.horizontalAdvance(token)

                    painter.drawText(
                        QtCore.QRect(
                            x_offset,
                            -3,
                            glyph_width,
                            self._glyph_height
                        ),
                        QtCore.Qt.AlignmentFlag.AlignCenter,
                        token
                    )
                    x_offset += glyph_width + self._spacing
                elif token.startswith("\uF448"):
                    glyph_width = \
                        self._render_vjoy_glyph(token.split(","), painter, x_offset)
                    x_offset += glyph_width + self._spacing
                elif len(token) == 1:
                    painter.setFont(self._bootstrap_font)
                    glyph_width = \
                        self._bootstrap_metrics.horizontalAdvance(token)

                    painter.drawText(
                        QtCore.QRect(
                            x_offset,
                            1,
                            glyph_width,
                            self._glyph_height
                        ),
                        QtCore.Qt.AlignmentFlag.AlignCenter,
                        token
                    )
                    x_offset += glyph_width + self._spacing
                else:
                    logging.getLogger("system").warning(
                        f"Unrecognized token in action string: '{token}'"
                    )
        finally:
            painter.end()

        # Render QPicture to QImage with exact size
        image = QtGui.QImage(
            max(20, x_offset - self._spacing if x_offset > 0 else 0),
            self._glyph_height,
            QtGui.QImage.Format.Format_ARGB32_Premultiplied
        )
        image.fill(QtCore.Qt.GlobalColor.transparent)

        img_painter = QtGui.QPainter(image)
        img_painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        img_painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
        img_painter.drawPicture(0, 0, picture)
        img_painter.end()

        return image

    def _render_vjoy_glyph(
        self,
        token: list[str],
        painter: QtGui.QPainter,
        x_offset: int
    ) -> int:
        """Renders a vJoy token.

        Token format: <vjoy_icon>,<device_id>,<type_letter>,<input_number>
        - vjoy_icon: Bootstrap icon character (\uF448)
        - device_id: vJoy device number
        - type_letter: A = Axis, B = Button, H = Hat
        - input_number: Input number (1-128)

        Args:
            token: The vJoy token string to parse and render
            painter: QPainter to render with
            x_offset: The x position to start rendering at

        Returns:
            Width of the rendered glyph in pixels
        """
        lookup = {
            "A": "AX",
            "B": "BTN",
            "H": "HAT"
        }
        vjoy_icon = token[0]
        vjoy_id = int(token[1])
        input_type = lookup[token[2]]
        input_id = int(token[3])

        # Calculate component widths
        icon_width = self._bootstrap_metrics.horizontalAdvance(vjoy_icon)
        device_width = self._segoe_metrics.horizontalAdvance(str(vjoy_id))
        label_block_width = max(
            self._vjoy_metrics.horizontalAdvance(str(input_id)),
            self._vjoy_metrics.horizontalAdvance(input_type)
        )

        current_x = x_offset

        # Draw vJoy icon
        painter.setFont(self._bootstrap_font)
        painter.drawText(
            QtCore.QRect(current_x, 1, icon_width, self._glyph_height),
            QtCore.Qt.AlignmentFlag.AlignCenter,
            vjoy_icon
        )
        current_x += icon_width + self._spacing

        # Draw device ID
        painter.setFont(self._segoe_font)
        painter.drawText(
            QtCore.QRect(current_x, -2, device_width, self._glyph_height),
            QtCore.Qt.AlignmentFlag.AlignVCenter,
            str(vjoy_id)
        )
        current_x += device_width + self._spacing

        # Draw input number (top)
        painter.setFont(self._vjoy_font)
        painter.drawText(
            QtCore.QRect(current_x, -1, label_block_width, 13),
            QtCore.Qt.AlignmentFlag.AlignCenter,
            str(input_id)
        )

        # Draw type label (bottom)
        painter.drawText(
            QtCore.QRect(current_x, 8, label_block_width, 13),
            QtCore.Qt.AlignmentFlag.AlignCenter,
            input_type
        )

        return icon_width + device_width + label_block_width + 2 * self._spacing

    def invalidate(self, action_string: str | None = None) -> None:
        """Invalidate cached images.

        Args:
            action_string: If provided, invalidate only this specific entry.
                If None, clear the entire cache.
        """
        with self._lock:
            if action_string is None:
                self._cache.clear()
            elif action_string in self._cache:
                del self._cache[action_string]
