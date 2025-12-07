// -*- coding: utf-8; -*-
//
// Copyright (C) 2020 Lionel Ott
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.


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

        textFromValue: function(value, locale) {
            return Number(value / decimalFactor)
                .toLocaleString(locale, "f", _root.decimals)
        }

        valueFromText: function(text, locale) {
            return Number.fromLocaleString(locale, text) * decimalFactor
        }

        onValueChanged: {
            _root.valueModified(toFloat(value))
        }
    }
}