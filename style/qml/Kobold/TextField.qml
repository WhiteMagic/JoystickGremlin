// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.TextField {
    id: control

    implicitHeight: Metrics.controlHeight
    implicitWidth: Math.max(Metrics.controlHeight * 6, contentWidth + leftPadding + rightPadding)
    leftPadding: Metrics.gapM
    rightPadding: Metrics.gapM

    color: control.enabled ? Theme.fg : Theme.fgDisabled
    selectionColor: Theme.bgSelected
    selectedTextColor: Theme.fg
    placeholderTextColor: Theme.fgMuted
    verticalAlignment: TextInput.AlignVCenter

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody

    background: Rectangle {
        radius: Metrics.radius
        color: Theme.bgAlt
        border.width: Metrics.hairline
        border.color: control.activeFocus ? Theme.accent : Theme.line
    }
}
