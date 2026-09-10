// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick

import Kobold.Foundation

Image {
    id: root

    property string name
    // Valid role values are: fg, fgMuted, fgDisabled, accent, error, warning.
    property string role: "fg"
    property int size: Metrics.icon

    readonly property color _color:
          role === "fgMuted"    ? Theme.fgMuted
        : role === "fgDisabled" ? Theme.fgDisabled
        : role === "accent"     ? Theme.accent
        : role === "error"      ? Theme.error
        : role === "warning"    ? Theme.warning
        :                         Theme.fg

    sourceSize: Qt.size(size, size)
    width: size
    height: size
    cache: true
    source: name === "" ? "" : "image://icon/" + name +
            "?c=" + _color.toString().slice(-6) + "&px=" + size
}
