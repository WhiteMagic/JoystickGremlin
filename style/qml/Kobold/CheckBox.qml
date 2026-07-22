// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.CheckBox {
    id: control

    implicitHeight: Metrics.ctrlH
    implicitWidth: contentItem.implicitWidth + leftPadding + rightPadding
    spacing: Metrics.gapM

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody

    // R4/SPEC §7: checked = accent border + accent tick, never a filled box.
    indicator: Rectangle {
        implicitWidth: Metrics.markSize
        implicitHeight: Metrics.markSize
        x: control.leftPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        radius: Metrics.radius
        color: "transparent"
        border.width: Metrics.hairline
        border.color: control.checked ? Theme.accent : Theme.line

        AppIcon {
            anchors.centerIn: parent
            name: "check"
            role: "accent"
            visible: control.checked
        }

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

    contentItem: Text {
        leftPadding: control.indicator.width + control.spacing
        text: control.text
        color: control.enabled ? Theme.fg : Theme.fgDisabled
        font: control.font
        verticalAlignment: Text.AlignVCenter
    }
}
