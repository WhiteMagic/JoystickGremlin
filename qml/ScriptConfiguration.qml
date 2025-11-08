// -*- coding: utf-8; -*-
//
// Copyright (C) 2025 Lionel Ott
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
import QtQuick.Dialogs
import QtQuick.Layouts
import Qt.labs.qmlmodels

import Gremlin.Plugin


JGListView {
    model: []
    delegate: _variableRenderer
    spacing: 10

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

                SpinBox {
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

                ComboBox {
                    Layout.alignment: Qt.AlignRight

                    model: backend.modeHierarchy.modeList

                    textRole: "name"
                    valueRole: "name"

                    onActivated: {
                        modelData.value = currentText
                    }

                    Component.onCompleted: function() {
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

                ComboBox {
                    Layout.alignment: Qt.AlignRight

                    model: modelData.options

                    onActivated: {
                        modelData.value = currentText
                    }

                    Component.onCompleted: function() {
                        currentIndex = find(modelData.value)
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

                JGTextInput {
                    Layout.alignment: Qt.AlignRight

                    Layout.fillWidth: true
                    text: modelData.value

                    onTextEdited: function() {
                        modelData.value = text
                    }
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
                    Layout.alignment: Qt.AlignRight

                    buttonLabel: modelData.label
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
                    Layout.alignment: Qt.AlignRight

                    validTypes: modelData.validTypes

                    onVjoyInputIdChanged: { modelData.inputId = vjoyInputId }
                    onVjoyDeviceIdChanged: { modelData.vjoyId = vjoyDeviceId }
                    onVjoyInputTypeChanged: { modelData.inputType = vjoyInputType }

                    Component.onCompleted: {
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
            color: parent.isValid ? "transparent" : "red"
        }

        Text {
            id: _text

            text: `${parent.text} ${modelData.isOptional ? '' : '(req)'}`

            Layout.minimumWidth: 150
            Layout.preferredWidth: 150

            font.pointSize: 11
            font.family: "Segoe UI"

            ToolTip {
                id: _tooltip
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