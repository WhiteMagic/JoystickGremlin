// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.ToolButton {
    id: control

    implicitHeight: Metrics.ctrlH
    implicitWidth: Math.max(Metrics.ctrlH, contentItem.implicitWidth + Metrics.gapM * 2)
    padding: Metrics.gapM

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody

    contentItem: Text {
        text: control.text
        color: control.enabled ? Theme.fg : Theme.fgDisabled
        font: control.font
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    // Flat: no border at rest -- only the fill responds, per its toolbar-affordance role.
    background: Rectangle {
        radius: Metrics.radius
        color: !control.enabled  ? "transparent"
             : control.down     ? Theme.bgSelected
             : control.hovered  ? Theme.bgHover
             :                    "transparent"

        Rectangle {
            visible: control.visualFocus
            anchors.fill: parent
            anchors.margins: -2
            radius: parent.radius
            color: "transparent"
            border.width: 2
            border.color: Theme.accent
        }
    }
}
