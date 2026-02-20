// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Gremlin.Style

// Visualizes the inputs and information about their associated actions
// contained in the LogicalDevice system.
Item {
    id: _root

    // property LogicalDeviceManagementModel device
    property int inputIndex
    property InputIdentifier inputIdentifier

    // Modal window to allow renaming of inputs.
    TextInputDialog {
        id: _textInput

        visible: false
        width: 300

        property var callback: null

        onAccepted: (value) => {
            callback(value)
            visible = false
        }
    }

    // List of all existing inputs.
    ColumnLayout {
        id: _content

        anchors.fill: parent

        JGListView {
            id: _inputList

            Layout.minimumWidth: 250
            Layout.fillHeight: true
            Layout.fillWidth: true
            scrollbarAlwaysVisible: true

            model: LogicalDeviceManagementModel {}
            delegate: _entryDelegate

            onCurrentIndexChanged: () => {
                inputIndex = currentIndex
                inputIdentifier = model.inputIdentifier(currentIndex)
            }
        }

        // Controls to add new logical device input instances.
        RowLayout {
            Layout.minimumWidth: 100
            Layout.preferredHeight: 50

            ComboBox {
                id: _input_type

                Layout.fillWidth: true

                model: ["Axis", "Button", "Hat"]
            }

            IconButton {
                Layout.preferredHeight: _input_type.height

                text: bsi.icons.add
                backgroundColor: Universal.chromeMediumColor

                onClicked: () => {
                    device.createInput(_input_type.currentValue)
                }
            }
        }
    }

    Component {
        id: _entryDelegate

        Item {
            id: _delegate

            height: _inputDisplay.height
            width: _inputDisplay.width

            required property int index
            required property string name
            required property string label
            required property int actionCount
            property ListView view: ListView.view
            property LogicalDeviceManagementModel model: view.model

            // Renders the entire "button" area of the singular input.
            Rectangle {
                id: _inputDisplay

                implicitWidth: view.width - _inputList.ScrollBar.vertical.width
                height: 50

                color: index == view.currentIndex
                    ? Universal.chromeMediumColor : Universal.background

                MouseArea {
                    anchors.fill: parent
                    onClicked: () => { view.currentIndex = index }
                }

                // User specified name assigned to this output.
                Label {
                    text: label
                    font.weight: 600

                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: 5
                    anchors.topMargin: 5
                }

                // Internally assigned sequential name.
                JGText {
                    text: name
                    anchors.leftMargin: 5
                    anchors.topMargin: 5

                    anchors.left: parent.left
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 2
                }

                Label {
                    text: actionCount ? actionCount : ""

                    anchors.top: parent.top
                    anchors.right: _btnTrash.left
                    anchors.rightMargin: 5
                    anchors.topMargin: 5
                }

                // Button to remove an input
                IconButton {
                    id: _btnTrash
                    text: bsi.icons.remove
                    font.pixelSize: 12

                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.rightMargin: 5
                    anchors.topMargin: 5

                    onClicked: () => { device.deleteInput(label) }
                }

                // Button enabling the editing of the input's label.
                IconButton {
                    id: _btnEdit
                    text: bsi.icons.edit
                    font.pixelSize: 12

                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.rightMargin: 5
                    anchors.bottomMargin: 2

                    onClicked: () => {
                        _textInput.text = label
                        _textInput.callback = (value) => {
                            device.changeName(label, value)
                        }
                        _textInput.visible = true
                    }
                }
            }
        }
    }
}
