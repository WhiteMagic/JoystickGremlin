// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T

import Kobold.Foundation

T.TextArea {
    id: control

    implicitWidth: Math.max(Metrics.controlHeight * 6,
                            implicitBackgroundWidth + leftInset + rightInset,
                            contentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(Metrics.controlHeight,
                             implicitBackgroundHeight + topInset + bottomInset,
                             contentHeight + topPadding + bottomPadding)
    leftPadding: Metrics.gapM
    rightPadding: Metrics.gapM
    topPadding: Metrics.gapS
    bottomPadding: Metrics.gapS

    color: control.enabled ? Theme.fg : Theme.fgDisabled
    selectionColor: Theme.bgSelected
    selectedTextColor: Theme.fg
    placeholderTextColor: Theme.fgMuted

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody

    background: Rectangle {
        radius: Metrics.radius
        color: Theme.bgAlt
        border.width: Metrics.hairline
        border.color: Theme.line
    }
}
