// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import Kobold.Foundation

// A flat structure label (SPEC §9): full action names, no icons, no
// abbreviations. `overflow` marks the trailing "+n" chip.
Rectangle {
    id: root

    property alias text: _label.text
    property bool overflow: false

    implicitWidth: _label.implicitWidth + Metrics.gapM
    implicitHeight: Metrics.textDetail + Metrics.gapM

    color: Theme.bgAlt
    border.width: Metrics.hairline
    border.color: Theme.line
    radius: Metrics.radius

    Text {
        id: _label
        anchors.centerIn: parent
        color: root.overflow ? Theme.fgMuted : Theme.fg
        font.family: FontType.sans
        font.pixelSize: Metrics.textDetail
        font.weight: FontType.regular
    }
}
