// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2020 Lionel Ott
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

    property real minValue
    property real maxValue
    property real stepSize
    property real value
    property int decimals: 2

    implicitWidth: _spinbox.width
    implicitHeight: _spinbox.height

    SpinBox {
        id: _spinbox

        value: _root.value * (10 ** _root.decimals)
        from: _root.minValue * (10 ** _root.decimals)
        to: _root.maxValue * (10 ** _root.decimals)
        stepSize: _root.stepSize * (10 ** _root.decimals)
        editable: true

        contentItem: TextInput {
            z: 2
            text: _spinbox.textFromValue(_spinbox.value, _spinbox.locale)

            font: _spinbox.font
            horizontalAlignment: Qt.AlignHCenter
            verticalAlignment: Qt.AlignVCenter

            readOnly: !_spinbox.editable
            validator: _spinbox.validator
            selectByMouse: true
            inputMethodHints: Qt.ImhFormattedNumbersOnly
        }

        validator: DoubleValidator {
            bottom: Math.min(_spinbox.from, _spinbox.to)
            top:  Math.max(_spinbox.from, _spinbox.to)
        }

        textFromValue: function(value, locale) {
            return Number(value / (10 ** _root.decimals)).toLocaleString(locale, "f", _root.decimals)
        }

        valueFromText: function(text, locale) {
            return Number.fromLocaleString(locale, text) * (10 ** _root.decimals)
        }

        onValueChanged: {
            _root.value = value / (10 ** _root.decimals)
        }
    }
}