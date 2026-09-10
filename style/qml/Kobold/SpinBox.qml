// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T

import Kobold.Foundation

T.SpinBox {
    id: control

    implicitHeight: Metrics.controlHeight
    implicitWidth: Metrics.controlHeight * 4

    leftPadding: down.indicator ? down.indicator.width : 0
    rightPadding: up.indicator ? up.indicator.width : 0

    editable: true
    wheelEnabled: true

    // Fixed-width numeric readout.
    font.family: FontType.mono
    font.pixelSize: Metrics.textBody

    contentItem: TextInput {
        text: control.displayText
        font: control.font
        color: control.enabled ? Theme.fg : Theme.fgDisabled
        selectionColor: Theme.bgSelected
        selectedTextColor: Theme.fg
        horizontalAlignment: Qt.AlignHCenter
        verticalAlignment: Qt.AlignVCenter
        readOnly: !control.editable
        validator: control.validator
        inputMethodHints: control.inputMethodHints
    }

    down.indicator: Rectangle {
        x: 0
        implicitWidth: Metrics.icon
        implicitHeight: control.height
        color: control.down.pressed ? Theme.bgSelected : control.down.hovered ? Theme.bgHover : Theme.bgAlt
        border.width: Metrics.hairline
        border.color: Theme.line

        Text {
            anchors.centerIn: parent
            text: "−"
            font: control.font
            color: control.enabled ? Theme.fg : Theme.fgDisabled
        }
    }

    up.indicator: Rectangle {
        x: control.width - width
        implicitWidth: Metrics.icon
        implicitHeight: control.height
        color: control.up.pressed ? Theme.bgSelected : control.up.hovered ? Theme.bgHover : Theme.bgAlt
        border.width: Metrics.hairline
        border.color: Theme.line

        Text {
            anchors.centerIn: parent
            text: "+"
            font: control.font
            color: control.enabled ? Theme.fg : Theme.fgDisabled
        }
    }

    background: Rectangle {
        radius: Metrics.radius
        color: Theme.bg
        border.width: Metrics.hairline
        border.color: control.activeFocus ? Theme.accent : Theme.line
    }
}
