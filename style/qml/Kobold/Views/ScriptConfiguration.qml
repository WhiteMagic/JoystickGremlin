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


ScrollList {
    model: []
    delegate: _variableRenderer
    spacing: Metrics.gapM

    DelegateChooser {
        id: _variableRenderer
        role: "type"

        DelegateChoice {
            roleValue: "bool"

            RowLayout {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: Metrics.gapM
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
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: Metrics.gapM
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
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: Metrics.gapM
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
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: Metrics.gapM
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
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: Metrics.gapM
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
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: Metrics.gapM
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
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: Metrics.gapM
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
                        width: contentWidth > 500 ? 500 : contentWidth + 20
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
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: Metrics.gapM
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
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: Metrics.gapM
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
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: Metrics.gapM
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
                width: contentWidth > 500 ? 500 : contentWidth + 20
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
