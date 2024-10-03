// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2024 Lionel Ott
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

import Gremlin.Profile
import Gremlin.ActionPlugins
import "../../qml"


Item {
    id: _root

    property MapToMouseModel action

    implicitHeight: _content.height

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        RowLayout {
            Label {
                id: _label

                Layout.preferredWidth: 50

                text: "<B>Mode</B>"
            }

            // Radio buttons to select the desired mapping mode
            RadioButton {
                id: _mode_button

                text: "Button"
                visible: inputBinding.behavior === "button"

                checked: _root.action.mode === "Button"
                onClicked: function () {
                    _root.action.mode = "Button"
                }

            }

            RadioButton {
                id: _mode_motion

                Layout.fillWidth: true

                text: "Motion"

                checked: _root.action.mode === "Motion"
                onClicked: function () {
                    _root.action.mode = "Motion"
                }
            }
        }

        RowLayout {
            visible: _mode_button.checked

            Label {
                text: "Mouse Button"
            }

            InputListener {
                callback: _root.action.updateInputs
                multipleInputs: false
                eventTypes: ["mouse"]

                buttonLabel: _root.action.button

                Component.onCompleted: function() {
                    console.log(inputBinding.behavior)
                }
            }

        }

        RowLayout {
            visible: _mode_motion.checked

            Label {
                text: "Mouse Motion"
            }


        }
    }
}