// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Kobold.Foundation
import Kobold.Controls

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
        width: Metrics.dp(300)

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

                    // Lazily-instantiated (Loader-created) Components don't
                    // see the delegate's own required properties by bare
                    // name -- go through the id instead. "label" is the
                    // model's raw rename/delete key, distinct from the
                    // display-only "name" InputButton already carries, so it
                    // isn't part of InputButton's own data contract.
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
            Layout.leftMargin: Metrics.gapM
            Layout.rightMargin: Metrics.gapM
            Layout.bottomMargin: Metrics.gapM

            AddActionMenuButton {
                Layout.fillWidth: true

                variant: "bordered"
                implicitHeight: Metrics.rowAction
                text: "Add input"
                model: ["Axis", "Button", "Hat"]
                // This pane is already bgAlt (_root.color above) -- raise both the button
                // fill and the popup to bg so neither blends into the page behind it.
                fillColor: Theme.bg
                menuColor: Theme.bg
                menuMatchesWidth: true
                // This control sits at the bottom of the input list -- pop the choices up
                // so the button stays the lowest thing on screen.
                menuOpensUpward: true

                onActionRequested: (name) => {
                    _inputList.model.createInput(name)
                }
            }
        }
    }
}
