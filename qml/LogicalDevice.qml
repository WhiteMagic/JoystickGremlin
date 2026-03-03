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

    property int inputIndex
    property InputIdentifier inputIdentifier
    property alias device: _inputList.model

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

            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.leftMargin: 10

            scrollbarAlwaysVisible: true
            spacing: 5

            model: LogicalDeviceManagementModel {}
            delegate: InputButton {
                width: _inputList.width - 30
                height: 50

                selected: model.index === _inputList.currentIndex
                onClicked: () => { _inputList.currentIndex = model.index }

                editButton: IconButton {
                    text: bsi.icons.edit
                    font.pixelSize: 12
                    width: 15

                    onClicked: () => {
                        _textInput.text = label
                        _textInput.callback = (value) => {
                            _inputList.model.changeName(label, value)
                        }
                        _textInput.visible = true
                    }
                }

                deleteButton: IconButton {
                    text: bsi.icons.remove
                    font.pixelSize: 12
                    width: 15

                    onClicked: () => { _inputList.model.deleteInput(label) }
                }
            }

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
                    _inputList.model.createInput(_input_type.currentValue)
                }
            }
        }
    }
}
