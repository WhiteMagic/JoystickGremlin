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

import QtQuick 2.14
import QtQuick.Controls 2.14


Item {
    id: root

    property real minValue
    property real maxValue
    property real stepSize
    property real value
    property int decimals: 2

    width: spinbox.width
    height: spinbox.height

    SpinBox {
        id: spinbox

        value: root.value * (10 ** root.decimals)
        from: root.minValue * (10 ** root.decimals)
        to: root.maxValue * (10 ** root.decimals)
        stepSize: root.stepSize * (10 ** root.decimals)
        editable: true

        contentItem: TextInput {
            z: 2
            text: spinbox.textFromValue(spinbox.value, spinbox.locale)

            font: spinbox.font
            horizontalAlignment: Qt.AlignHCenter
            verticalAlignment: Qt.AlignVCenter

            readOnly: !spinbox.editable
            validator: spinbox.validator
            selectByMouse: true
            inputMethodHints: Qt.ImhFormattedNumbersOnly
        }

        validator: DoubleValidator {
            bottom: Math.min(spinbox.from, spinbox.to)
            top:  Math.max(spinbox.from, spinbox.to)
        }

        textFromValue: function(value, locale) {
            return Number(value / (10 ** root.decimals)).toLocaleString(locale, "f", root.decimals)
        }

        valueFromText: function(text, locale) {
            return Number.fromLocaleString(locale, text) * (10 ** root.decimals)
        }

        onValueChanged: {
            root.value = value / (10 ** root.decimals)
        }
    }
}