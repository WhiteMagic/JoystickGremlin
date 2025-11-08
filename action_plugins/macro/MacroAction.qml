// -*- coding: utf-8; -*-
//
// Copyright (C) 2024 Lionel Ott
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

            LayoutHorizontalSpacer {}

            Label {
                text: "Repeat Mode"
            }

            ComboBox {
                id: _repeatMode

                textRole: "text"
                valueRole: "value"

                Component.onCompleted: function () {
                    currentIndex = indexOfValue(_root.action.repeatMode)
                }

                onActivated: function () {
                    _root.action.repeatMode = currentValue
                }

                model: [
                    {value: "single", text: "Single"},
                    {value: "count", text: "Count"},
                    {value: "toggle", text: "Togle"},
                    {value: "hold", text: "Hold"},
                ]
            }

            FloatSpinBox {
                visible: ["count", "toggle", "hold"].includes(_repeatMode.currentValue)

                value: _root.action.repeatDelay
                minValue: 0.0
                maxValue: 3600.0

                onValueModified: (newValue) => {
                    _root.action.repeatDelay = newValue
                }
            }

            SpinBox {
                visible: _repeatMode.currentValue === "count"

                value: _root.action.repeatCount
                from: 1
                to: 100
                editable: true

                onValueModified: function () {
                    _root.action.repeatCount = value
                }
            }

            LayoutHorizontalSpacer {}

            Switch {
                text: "Exclusive"

                checked: _root.action.isExclusive
                onClicked: () => _root.action.isExclusive = checked
            }

        }

        ActionDrop {
            targetIndex: 0
            insertionMode: "prepend"

            Layout.bottomMargin: -10
        }

        ListView {
            Layout.fillWidth: true
            implicitHeight: contentHeight
            spacing: 5

            model: _root.action.actions
            delegate: _delegateChooser
        }
    }

    // Renders the correct delegate based on the action type
    DelegateChooser {
        id: _delegateChooser

        role: "actionType"

        // Joystick action
        DelegateChoice {
            roleValue: "joystick"

            DraggableAction {
                icon: bsi.icons.icon_joystick
                label: "Joystick"

                actionItem: RowLayout {
                    InputListener {
                        buttonLabel: modelData.label
                        callback: (inputs) => {
                            modelData.updateJoystick(inputs)
                        }
                        multipleInputs: false
                        eventTypes: ["axis", "button", "hat"]
                    }

                    LayoutHorizontalSpacer {}

                    // Show different components based on input
                    PressOrRelease {
                        visible: modelData.inputType === "button"

                        checked: modelData.isPressed
                        onCheckedChanged: function () {
                            modelData.isPressed = checked
                        }
                    }
                    FloatSpinBox {
                        visible: modelData.inputType === "axis"

                        minValue: -1.0
                        maxValue: 1.0
                        value: modelData.axisValue

                        onValueModified: (newValue) => {
                            modelData.axisValue = newValue
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

                        Component.onCompleted: function () {
                            currentIndex = Qt.binding(
                                () => indexOfValue(modelData.hatDirection)
                            )
                        }

                        onActivated: function () {
                            modelData.hatDirection = currentValue
                        }
                    }
                }
            }
        }

        // Key action
        DelegateChoice {
            roleValue: "key"

            DraggableAction {
                icon: bsi.icons.icon_keyboard
                label: "Keyboard"

                actionItem: RowLayout {
                    InputListener {
                        buttonLabel: modelData.key
                        callback: (inputs) => { modelData.updateKey(inputs) }
                        multipleInputs: false
                        eventTypes: ["key"]
                    }

                    LayoutHorizontalSpacer {}

                    PressOrRelease {
                        checked: modelData.isPressed
                        onCheckedChanged: function () {
                            modelData.isPressed = checked
                        }
                    }
                }
            }
        }

        // Mouse button
        DelegateChoice {
            roleValue: "mouse-button"

            DraggableAction {
                icon: bsi.icons.icon_mouse
                label: "Mouse Button"

                actionItem: RowLayout {
                    InputListener {
                        buttonLabel: modelData.button
                        callback: (inputs) => { modelData.updateButton(inputs) }
                        multipleInputs: false
                        eventTypes: ["mouse"]
                    }

                    LayoutHorizontalSpacer {}

                    PressOrRelease {
                        checked: modelData.isPressed
                        onCheckedChanged: function () {
                            modelData.isPressed = checked
                        }
                    }
                }
            }
        }

        // Mouse motion
        DelegateChoice {
            roleValue: "mouse-motion"

            DraggableAction {
                icon: bsi.icons.icon_mouse
                label: "Mouse Motion"

                actionItem: RowLayout {
                    Label {
                        text: "X-Axis"
                    }
                    SpinBox {
                        value: modelData.dx
                        editable: true

                        onValueModified: function () {
                            modelData.dx = value
                        }
                    }

                    Label {
                        text: "Y-Axis"

                        leftPadding: 25
                    }
                    SpinBox {
                        value: modelData.dy
                        editable: true

                        onValueModified: function () {
                            modelData.dy = value
                        }
                    }

                    LayoutHorizontalSpacer {}
                }
            }
        }

        // Pause action
        DelegateChoice {
            roleValue: "pause"

            DraggableAction {
                icon: bsi.icons.icon_pause
                label: "Pause"

                actionItem: RowLayout {
                    FloatSpinBox {
                        minValue: 0.0
                        maxValue: 10.0
                        value: modelData.duration

                        onValueModified: (newValue) => {
                            modelData.duration = newValue
                        }
                    }
                    Label {
                        text: "seconds"
                    }
                    LayoutHorizontalSpacer {}
                }
            }
        }

        // vJoy action
        DelegateChoice {
            roleValue: "vjoy"

            DraggableAction {
                icon: bsi.icons.icon_joystick
                label: "vJoy"

                actionItem: RowLayout {
                    VJoySelector {
                        validTypes: ["axis", "button", "hat"]

                        onVjoyInputIdChanged: { modelData.inputId = vjoyInputId }
                        onVjoyDeviceIdChanged: { modelData.vjoyId = vjoyDeviceId }
                        onVjoyInputTypeChanged: { modelData.inputType = vjoyInputType }

                        Component.onCompleted: {
                            vjoyInputType = modelData.inputType
                            vjoyInputId = modelData.inputId
                            vjoyDeviceId = modelData.vjoyId
                        }
                    }

                    LayoutHorizontalSpacer {}

                    // Show different components based on input
                    PressOrRelease {
                        visible: modelData.inputType === "button"

                        checked: modelData.isPressed
                        onCheckedChanged: () => {
                            modelData.isPressed = checked
                        }
                    }
                    RowLayout {
                        visible: modelData.inputType === "axis"

                        FloatSpinBox {
                            minValue: -1.0
                            maxValue: 1.0
                            value: modelData.axisValue

                            onValueModified: (newValue) => {
                                modelData.axisValue = newValue
                            }
                        }
                        Label {
                            Layout.leftMargin: 50
                            text: "Mode: Relative"
                        }
                        Switch {
                            text:"Absolute"
                            checked: modelData.axisMode === "absolute"

                            onToggled: () => {
                                modelData.axisMode = checked ? "absolute" : "relative"
                            }
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
                        Component.onCompleted: () => {
                            currentIndex = Qt.binding(
                                () => {return indexOfValue(modelData.hatDirection)}
                            )
                        }

                        onActivated: () => {
                            modelData.hatDirection = currentValue
                        }
                    }
                }
            }
        }
    }


    // Predefined button that removes a given action
    component DeleteButton : IconButton {
        text: bsi.icons.remove
        font.pixelSize: 16

        onClicked: () => _root.action.removeAction(index)
    }

    // Switch with press/release labels for button action indication
    component PressOrRelease : Item {
        property alias checked: _porSwitch.checked

        implicitWidth: _porLayout.width
        implicitHeight: _porLayout.height

        RowLayout {
            id: _porLayout
            Label {
                text: "Release"
            }
            Switch {
                id: _porSwitch
                text: "Press"
            }
        }
    }

    // Displays an icon and also acts as the drag handle for the drag&drop
    // implementation
    component Icon : Label {
        property string iconName
        property var target

        property alias dragActive: _dragArea.drag.active

        text: bsi.icons.drag_handle + iconName

        font.pixelSize: 20

        MouseArea {
            id: _dragArea

            anchors.fill: parent

            drag.target: target
            drag.axis: Drag.YAxis

            // Create a visualization of the dragged item
            onPressed: function() {
                parent.parent.grabToImage(function(result) {
                    target.Drag.imageSource = result.url
                })
            }
        }
    }

    component ActionDrop : DropArea {
        property int targetIndex
        property string insertionMode: "append"

        height: 20

        Layout.fillWidth: true

        onDropped: function(drop) {
            drop.accept()
            _marker.opacity = 0.0
            _root.action.dropCallback(targetIndex, drop.text, insertionMode)
        }

        onEntered: function() {
            _marker.opacity = 1.0
        }
        onExited: function() {
            _marker.opacity = 0.0
        }

        Rectangle {
            anchors.fill: parent
            color: "transparent"

            Rectangle {
                id: _marker

                y: parent.y+5
                height: 10
                anchors.left: parent.left
                anchors.right: parent.right

                opacity: 0.0
                color: Universal.accent
            }
        }
    }

    component DraggableAction : ColumnLayout {
        id: _draggableAction

        // Widget properties
        property string icon
        property string label
        property alias actionItem: _actionLoader.sourceComponent

        // Ensure entire width is taken up
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 0

        // Define drag&drop behavior
        Drag.dragType: Drag.Automatic
        Drag.active: _icon.dragActive
        Drag.supportedActions: Qt.MoveAction
        Drag.proposedAction: Qt.MoveAction
        Drag.mimeData: {
            "text/plain": index.toString()
        }
        Drag.onDragFinished: function (action) {
            // If the drop action ought to be ignored, reset the UI by calling
            // the InputConfiguration.qml reload function.
            if (action === Qt.IgnoreAction) {
                reload();
            }
        }

        // Widget content assembly
        RowLayout {
            id: _actionContent

            Icon {
                id: _icon

                iconName: icon
                target: _draggableAction
            }

            Label {
                Layout.preferredWidth: 150
                text: label
            }

            // Holds action specific UI elements
            Loader {
                id: _actionLoader

                Layout.fillWidth: true
            }

            DeleteButton {}
        }

        ActionDrop {
            Layout.topMargin: -10
            Layout.bottomMargin: -10

            targetIndex: index
        }
    }

}