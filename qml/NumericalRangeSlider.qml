// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2019 Lionel Ott
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

    property real from
    property real to
    property real firstValue
    property real secondValue
    property real stepSize
    property int decimals

    height: Math.max(idSlider.height, idFirstValue.height, idSecondValue.height)
    width: idSlider.width + idFirstValue.width + idSecondValue.width


    property var validator: DoubleValidator {
        bottom: Math.min(root.from, root.to)
        top:  Math.max(root.from, root.to)
    }

    function textFromValue(value) {
        return Number(value).toLocaleString(Qt.locale(), "f", root.decimals)
    }

    function valueFromText(text) {
            return Number.fromLocaleString(Qt.locale(), text)
    }


    Rectangle {
        id: idFirstValue

        anchors.verticalCenter: idSlider.verticalCenter

        border.color: "#bdbebf"
        border.width: 2
        width: idFirstValueInput.width
        height: idFirstValueInput.height

        TextInput {
            id: idFirstValueInput

            padding: 5
            text: root.textFromValue(root.firstValue)

            font: idSlider.font
            horizontalAlignment: Qt.AlignHCenter
            verticalAlignment: Qt.AlignVCenter

            readOnly: false
            selectByMouse: true
            validator: root.validator
            inputMethodHints: Qt.ImhFormattedNumbersOnly

            onTextEdited: {
                var value = valueFromText(text)
                if(value >= root.secondValue)
                {
                    value = root.secondValue
                }
                root.firstValue = value
            }
        }
    }


    RangeSlider {
        id: idSlider

        anchors.left: idFirstValue.right

        from: root.from
        to: root.to
        first.value: root.firstValue
        second.value: root.secondValue
        stepSize: root.stepSize

        first.onMoved: {
            root.firstValue = first.value
        }
        second.onMoved: {
            root.secondValue = second.value
        }
    }

    Rectangle {
        id: idSecondValue

        anchors.left: idSlider.right
        anchors.verticalCenter: idSlider.verticalCenter

        border.color: "#bdbebf"
        border.width: 2
        width: idSecondValueInput.width
        height: idSecondValueInput.height

        TextInput {
            id: idSecondValueInput

            padding: 5
            text: root.textFromValue(root.secondValue)

            font: idSlider.font
            horizontalAlignment: Qt.AlignHCenter
            verticalAlignment: Qt.AlignVCenter

            readOnly: false
            selectByMouse: true
            validator: root.validator
            inputMethodHints: Qt.ImhFormattedNumbersOnly

            onTextEdited: {
                var value = valueFromText(text)
                if(value <= root.firstValue)
                {
                    value = root.firstValue
                }
                root.secondValue = value
            }

        }
    }

}