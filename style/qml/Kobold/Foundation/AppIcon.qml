// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import Kobold.Foundation

Image {
    id: root

    property string name
    property string role: "fg" // fg | fgMuted | fgDisabled | accent | error | warning

    readonly property color _c:
          role === "fgMuted"    ? Theme.fgMuted
        : role === "fgDisabled" ? Theme.fgDisabled
        : role === "accent"     ? Theme.accent
        : role === "error"      ? Theme.error
        : role === "warning"    ? Theme.warning
        :                         Theme.fg

    sourceSize: Qt.size(Metrics.icon, Metrics.icon)
    width: Metrics.icon
    height: Metrics.icon
    cache: true
    source: name === "" ? "" : "image://icon/" + name + "?c=" + _c.toString().slice(-6) + "&px=" + Metrics.icon
}
