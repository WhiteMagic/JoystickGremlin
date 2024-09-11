// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2022 Lionel Ott
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
import QtQuick.Layouts
import QtQuick.Window

import QtQuick.Controls.Universal


Window {
    id: _root

    minimumWidth: 200
    minimumHeight: 60

    color: Universal.background

    signal accepted(string value)
    property string text : "New text"
    property var validator: function(value) { return true }

    onTextChanged: function() {
        _input.focus = true
    }


    title: "Text Input Field"

    RowLayout {
        anchors.fill: parent

        TextInput {
            id: _input

            Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter
            Layout.fillWidth: true

            font.pixelSize: 15
            padding: 4

            text: _root.text

            onTextEdited: function()
            {
                let isValid = _root.validator(text)
                _outline.border.color = isValid ? Universal.accent : "red"
                _button.enabled = isValid
            }

            // Outline for the TextEdit field
            Rectangle {
                id: _outline
                anchors.fill: parent

                border {
                    color: Universal.accent
                    width: 1
                }
                z: -1
            }
        }

        Button {
            id: _button
            Layout.alignment: Qt.AlignVCenter | Qt.AlignHCenter

            text: "Ok"

            onClicked: function()
            {
                _root.accepted(_input.text)
            }
        }
    }

}