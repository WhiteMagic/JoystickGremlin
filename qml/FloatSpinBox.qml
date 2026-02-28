// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls


Item {
    id: _root

    property real minValue: -10.0
    property real maxValue: 10.0
    property real stepSize: 0.1
    property real value: 0.0
    property int decimals: 2
    property alias internalWidth: _spinbox.width
    property bool _internalUpdate: false

    readonly property int decimalFactor: Math.pow(10, _root.decimals)

    signal valueModified(real value)

    implicitWidth: _spinbox.width
    implicitHeight: _spinbox.height


    function toFloat(value) {
        return value / decimalFactor
    }

    function toInt(value) {
        return value * decimalFactor
    }

    // Calculate the width needed for the widest possible value.
    Component.onCompleted: {
        var testValues = [
            Number(minValue).toFixed(decimals),
            Number(maxValue).toFixed(decimals),
            Number(0).toFixed(decimals)
        ]

        for (var i = 0; i < testValues.length; i++) {
            _textMetrics.text = testValues[i]
            _spinbox.width = Math.max(_spinbox.width, _textMetrics.width)
        }

        _spinbox.width += 10
    }

    SpinBox {
        id: _spinbox

        value: toInt(_root.value)
        from: toInt(_root.minValue)
        to: toInt(_root.maxValue)
        stepSize: toInt(_root.stepSize)

        editable: true

        validator: DoubleValidator {
            bottom: Math.min(_spinbox.from, _spinbox.to)
            top:  Math.max(_spinbox.from, _spinbox.to)
            decimals: _root.decimals
            notation: DoubleValidator.StandardNotation
        }

        textFromValue: (value, locale) => {
            return Number(value / decimalFactor)
                .toLocaleString(locale, "f", _root.decimals)
        }

        valueFromText: (text, locale) => {
            return Number.fromLocaleString(locale, text) * decimalFactor
        }

        onValueChanged: () => {
            if (!_root._internalUpdate) {
                _root.valueModified(toFloat(value))
            }
        }
    }

    TextMetrics {
        id: _textMetrics
        font: _spinbox.font
    }
}
