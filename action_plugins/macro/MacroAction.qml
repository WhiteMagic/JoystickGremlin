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
import Qt.labs.qmlmodels

import QtQuick.Controls.Universal

import Gremlin.Profile
import Gremlin.ActionPlugins
import "../../qml"
import "../../qml/helpers.js" as Helpers


Item {
    id: _root

    property MacroModel action

    implicitHeight: _content.height

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right


        RowLayout {
            Layout.fillWidth: true

            Label {
                text: "<B>Macro Actions</B>"
            }

            ComboBox {
                id: _macroAction

                Layout.preferredWidth: 150

                textRole: "text"
                valueRole: "value"

                model: [
                    {value: "joystick", text: "Joystick"},
                    {value: "key", text: "Keyboard"},
                    {value: "mouse-button", text: "Mouse Button"},
                    {value: "mouse-motion", text: "Mouse Motion"},
                    {value: "pause", text: "Pause"},
                    {value: "vjoy", text: "vJoy"}
                ]
            }

            Button {
                text: "Add Action"

                onClicked: function() {
                    _root.action.addAction(_macroAction.currentValue)
                }
            }

            Rectangle {
                Layout.fillWidth: true
            }
        }

        ListView {
            Layout.fillWidth: true
            implicitHeight: contentHeight

            model: _root.action.actions
            delegate: _delegateChooser
            spacing: 5
        }
    }

    // Renders the correct delegate based on the action type
    DelegateChooser {
        id: _delegateChooser

        role: "actionType"

        // Joystick action
        DelegateChoice {
            roleValue: "joystick"

            RowLayout {
                anchors.left: parent.left
                anchors.right: parent.right

                Icon {
                    text: Constants.icon_joystick
                }
                InputListener {
                    buttonLabel: modelData.label
                    callback: modelData.updateJoystick
                    multipleInputs: false
                    eventTypes: ["axis", "button", "hat"]
                }

                // Show different components based on input
                Switch {
                    visible: modelData.inputType === "button"

                    text: "Key Pressed"
                    checked: modelData.isPressed

                    onToggled: function()
                    {
                        modelData.isPressed = checked
                    }
                }
                FloatSpinBox {
                    visible: modelData.inputType === "axis"

                    minValue: -1.0
                    maxValue: 1.0
                    realValue: modelData.axisValue

                    onRealValueModified: function() {
                        modelData.axisValue = realValue
                    }
                }
                ComboBox {
                    visible: modelData.inputType === "hat"

                    textRole: "text"
                    valueRole: "value"

                    model: [
                        {value: "center", text: "Center"},
                        {value: "north", text: "North"},
                        {value: "north-east", text: "North East"},
                        {value: "east", text: "East"},
                        {value: "south-east", text: "South East"},
                        {value: "south", text: "South"},
                        {value: "south-west", text: "South West"},
                        {value: "west", text: "West"},
                        {value: "north-west", text: "North West"}
                    ]

                    currentIndex: indexOfValue(modelData.hatDirection)
                    Component.onCompleted: function() {
                        currentIndex = indexOfValue(modelData.hatDirection)
                    }

                    onActivated: function() {
                        modelData.hatDirection = currentValue
                    }
                }

                Filler {}
                DeleteButton {}
            }
        }

        // Key action
        DelegateChoice {
            roleValue: "key"

            RowLayout {
                anchors.left: parent.left
                anchors.right: parent.right

                Icon {
                    text: Constants.icon_keyboard
                }
                Label {
                    text: "Key"
                }

                InputListener {
                    buttonLabel: modelData.key
                    callback: modelData.updateKey
                    multipleInputs: false
                    eventTypes: ["key"]
                }

                Switch {
                    text: "Key Pressed"
                    checked: modelData.isPressed

                    onToggled: function()
                    {
                        modelData.isPressed = checked
                    }
                }

                Filler {}
                DeleteButton {}
            }
        }

        // Mouse button
        DelegateChoice {
            roleValue: "mouse-button"

            RowLayout {
                anchors.left: parent.left
                anchors.right: parent.right

                Icon {
                    text: Constants.icon_mouse
                }
                Label {
                    text: "Mouse Button"
                }

                InputListener {
                    buttonLabel: modelData.button
                    callback: modelData.updateButton
                    multipleInputs: false
                    eventTypes: ["mouse"]
                }

                Switch {
                    text: "Key Pressed"
                    checked: modelData.isPressed

                    onToggled: function()
                    {
                        modelData.isPressed = checked
                    }
                }

                Filler {}
                DeleteButton {}
            }
        }

        // Mouse motion
        DelegateChoice {
            roleValue: "mouse-motion"

            RowLayout {
                anchors.left: parent.left
                anchors.right: parent.right

                Icon {
                    text: Constants.icon_mouse
                }
                Label {
                    text: "Mouse Motion"
                }
                Label {
                    text: "X-Axis"
                }
                SpinBox {
                    value: modelData.dx
                    editable: true

                    onValueModified: function() {
                        modelData.dx = value
                    }
                }
                Label {
                    text: "Y-Axis"
                }
                SpinBox {
                    value: modelData.dy
                    editable: true

                    onValueModified: function() {
                        modelData.dy = value
                    }
                }

                Filler {}
                DeleteButton {}
            }
        }

        // Pause action
        DelegateChoice {
            roleValue: "pause"

            RowLayout {
                anchors.left: parent.left
                anchors.right: parent.right

                Icon {
                    text: Constants.icon_pause
                }
                Label {
                    text: "Pause Duration"
                }
                FloatSpinBox {
                    minValue: 0.0
                    maxValue: 10.0
                    realValue: modelData.duration

                    onRealValueModified: function() {
                        modelData.duration = realValue
                    }
                }
                Filler {}
                DeleteButton {}
            }
        }

        // vJoy action
        DelegateChoice {
            roleValue: "vjoy"

            RowLayout {
                anchors.left: parent.left
                anchors.right: parent.right

                Icon {
                    text: Constants.icon_joystick
                }
                VJoySelector {
                    vjoyInputType: modelData.inputType
                    vjoyInputId: modelData.inputId
                    vjoyDeviceId: modelData.vjoyId
                    validTypes: ["axis", "button", "hat"]

                    onVjoyInputIdChanged: { modelData.inputId = vjoyInputId }
                    onVjoyDeviceIdChanged: { modelData.vjoyId = vjoyDeviceId }
                    onVjoyInputTypeChanged: { modelData.inputType = vjoyInputType }
                }

                // Show different components based on input
                Switch {
                    visible: modelData.inputType === "button"

                    text: "Key Pressed"
                    checked: modelData.isPressed

                    onToggled: function()
                    {
                        modelData.isPressed = checked
                    }
                }
                FloatSpinBox {
                    visible: modelData.inputType === "axis"

                    minValue: -1.0
                    maxValue: 1.0
                    realValue: modelData.axisValue

                    onRealValueModified: function() {
                        modelData.axisValue = realValue
                    }
                }
                ComboBox {
                    visible: modelData.inputType === "hat"

                    textRole: "text"
                    valueRole: "value"

                    model: [
                        {value: "center", text: "Center"},
                        {value: "north", text: "North"},
                        {value: "north-east", text: "North East"},
                        {value: "east", text: "East"},
                        {value: "south-east", text: "South East"},
                        {value: "south", text: "South"},
                        {value: "south-west", text: "South West"},
                        {value: "west", text: "West"},
                        {value: "north-west", text: "North West"}
                    ]

                    currentIndex: indexOfValue(modelData.hatDirection)
                    Component.onCompleted: function() {
                        currentIndex = indexOfValue(modelData.hatDirection)
                    }

                    onActivated: function() {
                        modelData.hatDirection = currentValue
                    }
                }

                Filler {}
                DeleteButton {}
            }
        }
    }

    component Filler : Rectangle {
        Layout.fillWidth: true
    }

    component DeleteButton : IconButton {
        text: Constants.remove
        font.pixelSize: 16

        onClicked: function() {
            console.log(index)
        }
    }

    component Icon : Label {
        font.pixelSize: 20
    }

}