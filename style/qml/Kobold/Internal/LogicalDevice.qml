// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Gremlin.Style
import Kobold.Foundation
import Kobold.Controls

// TextInputDialog is a plain reusable dialog kept in qml/ (not
// Kobold-specific); reach it via a relative directory import since it's
// outside this module's own folder.
import "../../../../qml"

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

        InputListView {
            id: _inputList

            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.leftMargin: Metrics.gapM

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

        // Controls to add new logical device input instances.
        RowLayout {
            Layout.minimumWidth: 100
            Layout.preferredHeight: 50

            ComboBox {
                id: _input_type

                Layout.fillWidth: true
                Layout.leftMargin: 5

                model: ["Axis", "Button", "Hat"]
            }

            Button {
                Layout.preferredHeight: _input_type.height
                Layout.rightMargin: 5

                text: bsi.icons.add
                font.family: "bootstrap-icons"

                onClicked: () => {
                    _inputList.model.createInput(_input_type.currentValue)
                }
            }
        }
    }
}
