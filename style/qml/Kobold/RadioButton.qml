// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.RadioButton {
    id: control

    implicitHeight: Metrics.controlHeight
    implicitWidth: contentItem.implicitWidth + leftPadding + rightPadding
    spacing: Metrics.gapM

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody

    // R4/SPEC §7: checked = accent ring + accent dot, never a filled box.
    indicator: Rectangle {
        implicitWidth: Metrics.icon
        implicitHeight: Metrics.icon
        x: control.leftPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        radius: width / 2
        color: "transparent"
        border.width: Metrics.hairline
        border.color: control.checked ? Theme.accent : Theme.line

        Rectangle {
            anchors.centerIn: parent
            width: parent.width - Metrics.gapS * 2
            height: width
            radius: width / 2
            color: Theme.accent
            visible: control.checked
        }

        Rectangle {
            visible: control.visualFocus
            anchors.fill: parent
            anchors.margins: -2
            radius: width / 2
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
