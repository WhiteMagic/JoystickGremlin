// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kobold.Foundation

// Public plugin-facing kit component: a labelled numeric range -- two mono-font value fields
// either side of a RangeSlider. Prop-in/signal-out, like the app's other reusable components
// (ActionRow, ActivationToggle, SlotHeader) -- never writes back to its own input properties.
RowLayout {
    id: root

    property real from: 0
    property real to: 1
    property real firstValue: 0
    property real secondValue: 1
    property real stepSize: 0
    property int decimals: 2

    signal firstValueEdited(real value)
    signal secondValueEdited(real value)

    spacing: Metrics.gapM

    property var _validator: DoubleValidator {
        bottom: Math.min(root.from, root.to)
        top: Math.max(root.from, root.to)
        decimals: root.decimals
    }

    function _textFromValue(value) {
        return Number(value).toLocaleString(Qt.locale(), "f", root.decimals)
    }

    function _valueFromText(text) {
        return Number.fromLocaleString(Qt.locale(), text)
    }

    TextField {
        id: _firstInput

        Layout.preferredWidth: Metrics.ctrlH * 3
        horizontalAlignment: TextInput.AlignHCenter
        font.family: FontType.mono
        font.pixelSize: Metrics.textBody
        validator: root._validator
        inputMethodHints: Qt.ImhFormattedNumbersOnly
        selectByMouse: true

        text: root._textFromValue(root.firstValue)

        onEditingFinished: {
            const value = root._valueFromText(text)
            root.firstValueEdited(Math.min(value, root.secondValue))
        }
    }

    RangeSlider {
        id: _slider

        Layout.fillWidth: true
        Layout.preferredWidth: Metrics.ctrlH * 6

        from: root.from
        to: root.to
        stepSize: root.stepSize
        first.value: root.firstValue
        second.value: root.secondValue

        first.onMoved: root.firstValueEdited(first.value)
        second.onMoved: root.secondValueEdited(second.value)
    }

    TextField {
        id: _secondInput

        Layout.preferredWidth: Metrics.ctrlH * 3
        horizontalAlignment: TextInput.AlignHCenter
        font.family: FontType.mono
        font.pixelSize: Metrics.textBody
        validator: root._validator
        inputMethodHints: Qt.ImhFormattedNumbersOnly
        selectByMouse: true

        text: root._textFromValue(root.secondValue)

        onEditingFinished: {
            const value = root._valueFromText(text)
            root.secondValueEdited(Math.max(value, root.firstValue))
        }
    }
}
