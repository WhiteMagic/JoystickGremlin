// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.MenuBarItem {
    id: control

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset,
                             implicitContentHeight + topPadding + bottomPadding)

    padding: Metrics.gapM

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody

    contentItem: Text {
        text: control.text
        font: control.font
        color: control.enabled ? Theme.fg : Theme.fgDisabled
        verticalAlignment: Text.AlignVCenter
    }

    // Hover/open = bgHover only (mockup's `.menubar span:hover`); never accent-filled (R4).
    background: Rectangle {
        implicitHeight: Metrics.menuBar
        color: control.down || control.highlighted ? Theme.bgHover : "transparent"
    }
}
