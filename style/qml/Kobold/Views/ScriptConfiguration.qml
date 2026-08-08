// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import Qt.labs.qmlmodels

import Gremlin.Profile
import Gremlin.Script

import Kobold.Controls
import Kobold.Foundation


// Wrapper Item, not a bare ScrollList -- a ScrollList placed directly as a
// SplitView child has its geometry driven by the SplitView itself, so
// anchors.fill/leftMargin/topMargin on the list (the DeviceInputList.qml
// pattern) need a plain Item parent to anchor against. ScriptManager.qml
// sets `.model` on this component from the outside, hence the alias.
Item {
    id: _root

    property alias model: _list.model

    ScrollList {
        id: _list

        anchors.fill: parent
        anchors.leftMargin: Metrics.gapM
        anchors.topMargin: Metrics.gapM

        model: []
        delegate: _variableRenderer
        spacing: Metrics.gapM

        footer: Item {
            width: ListView.view.width
            height: Metrics.gapM
        }

        DelegateChooser {
            id: _variableRenderer
            role: "type"

            DelegateChoice {
                roleValue: "bool"

                RowLayout {
                    width: ListView.view.width - Metrics.gapM * 2
                    spacing: Metrics.gapM

                    DescriptiveText {
                        text: modelData.name
                        description: modelData.description
                        isValid: modelData.isValid
                    }

                    CheckBox {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignTop | Qt.AlignRight

                        checked: modelData.value

                        onToggled: () => modelData.value = checked
                    }
                }
            }

            DelegateChoice {
                roleValue: "float"

                RowLayout {
                    width: ListView.view.width - Metrics.gapM * 2
                    spacing: Metrics.gapM

                    DescriptiveText {
                        text: modelData.name
                        description: modelData.description
                        isValid: modelData.isValid
                    }

                    DoubleSpinBox {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignRight

                        from: modelData.minValue
                        to: modelData.maxValue
                        value: modelData.value

                        onValueModified: (newValue) => {
                            modelData.value = newValue
                        }
                    }
                }
            }

            DelegateChoice {
                roleValue: "int"

                RowLayout {
                    width: ListView.view.width - Metrics.gapM * 2
                    spacing: Metrics.gapM

                    DescriptiveText {
                        text: modelData.name
                        description: modelData.description
                        isValid: modelData.isValid
                    }

                    SpinBox {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignRight

                        editable: true
                        from: modelData.minValue
                        to: modelData.maxValue
                        value: modelData.value

                        onValueModified: function () {
                            modelData.value = value
                        }
                    }
                }
            }

            DelegateChoice {
                roleValue: "keyboard"

                RowLayout {
                    width: ListView.view.width - Metrics.gapM * 2
                    spacing: Metrics.gapM

                    DescriptiveText {
                        text: modelData.name
                        description: modelData.description
                        isValid: modelData.isValid
                    }

                    InputCaptureButton {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignRight

                        text: modelData.label
                        callback: (inputs) => { modelData.updateKeyboard(inputs) }
                        multipleInputs: false
                        eventTypes: ["key"]
                    }
                }
            }

            DelegateChoice {
                roleValue: "logical-device"

                RowLayout {
                    width: ListView.view.width - Metrics.gapM * 2
                    spacing: Metrics.gapM

                    DescriptiveText {
                        text: modelData.name
                        description: modelData.description
                        isValid: modelData.isValid
                    }

                    LogicalDeviceSelector {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignRight

                        validTypes: modelData.validTypes
                        logicalInputIdentifier: modelData.logicalInputIdentifier

                        onLogicalInputIdentifierChanged: () => {
                            modelData.logicalInputIdentifier = logicalInputIdentifier
                        }
                    }
                }
            }

            DelegateChoice {
                roleValue: "mode"

                RowLayout {
                    width: ListView.view.width - Metrics.gapM * 2
                    spacing: Metrics.gapM

                    DescriptiveText {
                        text: modelData.name
                        description: modelData.description
                        isValid: modelData.isValid
                    }

                    ComboBox {
                        id: _mode

                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignRight

                        model: ModeListModel {}
                        textRole: "name"
                        valueRole: "name"

                        onActivated: () => { modelData.value = currentText }

                        Component.onCompleted: () => {
                            currentIndex = find(modelData.value)
                        }
                    }
                }
            }

            DelegateChoice {
                roleValue: "selection"

                RowLayout {
                    width: ListView.view.width - Metrics.gapM * 2
                    spacing: Metrics.gapM

                    DescriptiveText {
                        text: modelData.name
                        description: modelData.description
                        isValid: modelData.isValid
                    }

                    ComboBox {
                        id: _selection

                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignRight

                        model: modelData.options

                        onActivated: () => { modelData.value = currentText }

                        Component.onCompleted: () => {
                            currentIndex = find(modelData.value)
                        }

                        ToolTip {
                            text: parent.currentText
                            // Set an upper width of the tooltip to force word wrap
                            // on long selection names.
                            width: Metrics.tooltipWidth(contentWidth)
                            visible: _hoverHandler.hovered
                            delay: 500
                        }

                        HoverHandler {
                            id: _hoverHandler
                            acceptedDevices: PointerDevice.Mouse |
                                PointerDevice.TouchPad
                        }
                    }
                }
            }

            DelegateChoice {
                roleValue: "string"

                RowLayout {
                    width: ListView.view.width - Metrics.gapM * 2
                    spacing: Metrics.gapM

                    DescriptiveText {
                        text: modelData.name
                        description: modelData.description
                        isValid: modelData.isValid
                    }

                    TextField {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignRight

                        text: modelData.value

                        onTextEdited: () => { modelData.value = text }
                    }
                }
            }

            DelegateChoice {
                roleValue: "physical-input"

                RowLayout {
                    width: ListView.view.width - Metrics.gapM * 2
                    spacing: Metrics.gapM

                    DescriptiveText {
                        text: modelData.name
                        description: modelData.description
                        isValid: modelData.isValid
                    }

                    InputCaptureButton {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignRight

                        text: modelData.label
                        callback: (inputs) => { modelData.updateJoystick(inputs) }
                        multipleInputs: false
                        eventTypes: modelData.validTypes
                    }
                }
            }

            DelegateChoice {
                roleValue: "vjoy"

                RowLayout {
                    width: ListView.view.width - Metrics.gapM * 2
                    spacing: Metrics.gapM

                    DescriptiveText {
                        text: modelData.name
                        description: modelData.description
                        isValid: modelData.isValid
                    }

                    VJoySelector {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignRight

                        validTypes: modelData.validTypes

                        onSelectionChanged: (vjoyId, inputType, inputId) => {
                            modelData.vjoyId = vjoyId
                            modelData.inputType = inputType
                            modelData.inputId = inputId
                        }

                        Component.onCompleted: () => {
                            initialize(
                                modelData.vjoyId,
                                modelData.inputType,
                                modelData.inputId
                            )
                        }
                    }
                }
            }

        }

        component DescriptiveText : RowLayout {
            id: _descriptiveText

            property string text: ""
            property alias description: _tooltip.text
            property bool isValid: false

            spacing: Metrics.gapS

            AppIcon {
                visible: !_descriptiveText.isValid
                name: "error"
                role: "error"
            }

            Label {
                id: _text

                text: modelData.isOptional ?
                    _descriptiveText.text : `${_descriptiveText.text} (req)`
                wrapMode: Text.WordWrap

                Layout.preferredWidth: Metrics.labelColumn

                ToolTip {
                    id: _tooltip
                    // Set an upper width of the tooltip to force word wrap on
                    // long description texts.
                    width: Metrics.tooltipWidth(contentWidth)
                    visible: _hoverHandler.hovered
                    delay: 500
                }

                HoverHandler {
                    id: _hoverHandler
                    acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                }
            }
        }
    }
}
