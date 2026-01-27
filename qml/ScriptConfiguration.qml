// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import Qt.labs.qmlmodels

import Gremlin.Profile
import Gremlin.Script
import Gremlin.Style

JGListView {
    model: []
    delegate: _variableRenderer
    spacing: 10

    readonly property int labelWidth: 250

    DelegateChooser {
        id: _variableRenderer
        role: "type"

        DelegateChoice {
            roleValue: "bool"

            RowLayout {
                id: _layout

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: 10

                DescriptiveText {
                    text: modelData.name
                    description: modelData.description
                    isValid: modelData.isValid
                }

                Switch {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop | Qt.AlignRight

                    checked: modelData.value
                    text: checked ? "On" : "Off"

                    onToggled: () => modelData.value = checked
                }
            }
        }

        DelegateChoice {
            roleValue: "float"

            RowLayout {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: 10

                DescriptiveText {
                    text: modelData.name
                    description: modelData.description
                    isValid: modelData.isValid
                }

                FloatSpinBox {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignRight

                    minValue: modelData.minValue
                    maxValue: modelData.maxValue
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
                anchors.margins: 10

                DescriptiveText {
                    text: modelData.name
                    description: modelData.description
                    isValid: modelData.isValid
                }

                JGSpinBox {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignRight

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
                anchors.margins: 10

                DescriptiveText {
                    text: modelData.name
                    description: modelData.description
                    isValid: modelData.isValid
                }

                InputListener {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignRight

                    buttonLabel: modelData.label
                    buttonWidth: width
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
                anchors.margins: 10

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
                anchors.margins: 10

                DescriptiveText {
                    text: modelData.name
                    description: modelData.description
                    isValid: modelData.isValid
                }

                JGComboBox {
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
                anchors.margins: 10

                DescriptiveText {
                    text: modelData.name
                    description: modelData.description
                    isValid: modelData.isValid
                }

                JGComboBox {
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
                anchors.margins: 10

                DescriptiveText {
                    text: modelData.name
                    description: modelData.description
                    isValid: modelData.isValid
                }

                JGTextField {
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
                anchors.margins: 10

                DescriptiveText {
                    text: modelData.name
                    description: modelData.description
                    isValid: modelData.isValid
                }

                InputListener {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignRight

                    buttonLabel: modelData.label
                    buttonWidth: width
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
                anchors.margins: 10

                DescriptiveText {
                    text: modelData.name
                    description: modelData.description
                    isValid: modelData.isValid
                }

                VJoySelector {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignRight

                    validTypes: modelData.validTypes

                    onVjoyInputIdChanged: () => {
                        modelData.inputId = vjoyInputId
                    }
                    onVjoyDeviceIdChanged: () => {
                        modelData.vjoyId = vjoyDeviceId
                    }
                    onVjoyInputTypeChanged: () => {
                        modelData.inputType = vjoyInputType
                    }

                    Component.onCompleted: () => {
                        vjoyInputType = modelData.inputType
                        vjoyInputId = modelData.inputId
                        vjoyDeviceId = modelData.vjoyId
                    }
                }
            }
        }

    }

    component DescriptiveText : RowLayout {
        property string text: ""
        property alias description: _tooltip.text
        property bool isValid: false

        Rectangle {
            id: _marker

            width: 5
            Layout.fillHeight: true
            color: parent.isValid ? "transparent" : Style.error
        }

        JGText {
            id: _text

            font.pointSize: 11
            text: `${parent.text} ${modelData.isOptional ? '' : '(req)'}`
            wrapMode: Text.WordWrap

            Layout.minimumWidth: 150
            Layout.preferredWidth: labelWidth

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
