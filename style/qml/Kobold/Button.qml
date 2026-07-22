// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.Button {
    id: control

    implicitHeight: Metrics.ctrlH
    implicitWidth: Math.max(Metrics.ctrlH * 2, contentItem.implicitWidth + Metrics.gapM * 2)
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

    background: Rectangle {
        radius: Metrics.radius
        color: !control.enabled ? Theme.bgAlt
             : control.down     ? Theme.bgSelected
             : control.hovered  ? Theme.bgHover
             :                    Theme.bgAlt
        border.width: Metrics.hairline
        border.color: Theme.line

        // Focus ring: 2px accent outline, offset -2px (R4 -- accent is state only, never a fill).
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
