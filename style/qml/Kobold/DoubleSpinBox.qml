// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

// Native Qt 6.11 double-valued spin box (QtQuick.Templates/DoubleSpinBox) -- real
// from/to/value/stepSize doubles plus a decimals property, no scaled-integer emulation
// needed (that hack is what the old qml/FloatSpinBox.qml existed for).
T.DoubleSpinBox {
    id: control

    implicitHeight: Metrics.controlHeight
    implicitWidth: Metrics.controlHeight * 4

    // Every historical caller of the old FloatSpinBox needed typed entry, not just
    // +/- stepping -- unlike the plain integer SpinBox.qml, editable is on by default.
    editable: true

    // Inset the content item between the two indicators -- padding on the TextInput
    // itself only insets its glyphs, not its hit region, which otherwise spans the full
    // control width and swallows clicks meant for the indicator buttons underneath it.
    leftPadding: down.indicator ? down.indicator.width : 0
    rightPadding: up.indicator ? up.indicator.width : 0

    wheelEnabled: true

    // Fixed-width numeric readout (SPEC §5): mono, not sans.
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
        implicitWidth: Metrics.dp(18)
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
        implicitWidth: Metrics.dp(18)
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
