// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Kobold.Controls
import Kobold.Foundation

// Visualizes the inputs and information about their associated actions
// contained in the LogicalDevice system.
Rectangle {
    id: _root

    color: Theme.bgAlt

    property int inputIndex
    property InputIdentifier inputIdentifier
    property alias device: _inputList.model

    // Modal window to allow renaming of inputs.
    TextInputDialog {
        id: _textInput

        visible: false

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

        ScrollList {
            id: _inputList

            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.leftMargin: Metrics.gapM
            Layout.topMargin: Metrics.gapM

            scrollbarAlwaysVisible: true
            spacing: Metrics.gapS
            reuseItems: true

            model: LogicalDeviceManagementModel {}

            delegate: InputButton {
                id: _row

                width: _inputList.width - Metrics.gapM * 2
                height: Metrics.rowInput

                selected: index === _inputList.currentIndex
                onClicked: () => { _inputList.currentIndex = index }

                editButton: ToolButton {
                    icon.name: "edit"
                    padding: Metrics.gapS

                    onClicked: () => {
                        const label = _inputList.model.labelAt(_row.index)
                        _textInput.text = label
                        _textInput.callback = (value) => {
                            _inputList.model.changeName(label, value)
                        }
                        _textInput.visible = true
                    }
                }

                deleteButton: ToolButton {
                    icon.name: "delete"
                    padding: Metrics.gapS

                    onClicked: () => {
                        _inputList.model.deleteInput(_inputList.model.labelAt(_row.index))
                    }
                }
            }

            footer: Item {
                width: ListView.view.width
                height: Metrics.gapM
            }

            onCurrentIndexChanged: () => {
                inputIndex = currentIndex
                inputIdentifier = model.inputIdentifier(currentIndex)
            }
        }

        // Control to add new logical device input instances.
        RowLayout {
            Layout.fillWidth: true
            Layout.margins: Metrics.gapL

            AddActionMenuButton {
                Layout.fillWidth: true

                text: "Add input"
                model: ["Axis", "Button", "Hat"]

                variant: "bordered"
                implicitHeight: Metrics.rowAction

                // Adjust colors to match with the left panel, and open upwards.
                fillColor: Theme.bg
                menuColor: Theme.bg
                menuMatchesWidth: true
                menuOpensUpward: true

                onActionRequested: (name) => {
                    _inputList.model.createInput(name)
                }
            }
        }
    }
}
