// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.ToolTip {
    id: control

    delay: 500
    // T.ToolTip supplies no default position -- that's the style's job here.
    x: parent ? Math.round((parent.width - width) / 2) : 0
    y: -implicitHeight - Metrics.gapS
    leftPadding: Metrics.gapM
    rightPadding: Metrics.gapM
    topPadding: Metrics.gapS
    bottomPadding: Metrics.gapS

    implicitWidth: contentItem.implicitWidth + leftPadding + rightPadding
    implicitHeight: contentItem.implicitHeight + topPadding + bottomPadding

    contentItem: Text {
        text: control.text
        color: Theme.fg
        font.family: FontType.sans
        font.pixelSize: Metrics.textDetail
        wrapMode: Text.WordWrap
    }

    // No shadow, no elevation (R2): opaque fill + 1px line border, same as Menu/ComboBox popups.
    background: Rectangle {
        color: Theme.bgAlt
        border.width: Metrics.hairline
        border.color: Theme.line
    }
}
