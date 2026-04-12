// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.ActionPlugins
import Gremlin.Profile
import Gremlin.Style
import Gremlin.Util
import "../../qml"

Item {
    id: _root

    property ConditionModel action
    readonly property int conditionLabelWidth: 150

    implicitHeight: _content.height

    // Turns the list of entries into an unordered HTML element.
    function toUnorderedList(entries) {
        return entries.join("<br>")
    }

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        // +-------------------------------------------------------------------
        // | Logical condition setup
        // +-------------------------------------------------------------------
        RowLayout {
            id: _logicalOperator

            Layout.fillWidth: true

            Label {
                text: "When "
            }
            ComboBox {
                id: _logicalOperatorSelector
                model: _root.action.logicalOperators

                textRole: "text"
                valueRole: "value"

                Component.onCompleted: () => {
                    currentIndex = indexOfValue(_root.action.logicalOperator)
                }

                onActivated: () => {
                    _root.action.logicalOperator = currentValue
                }
            }
            Label {
                text: "of the following conditions are met"
            }

            LayoutHorizontalSpacer {}

            Button {
                text: "Add Condition"

                onClicked: () => {
                    _root.action.addCondition(_condition.currentValue)
                }
            }

            ComboBox {
                id: _condition

                implicitContentWidthPolicy: ComboBox.WidestText
                textRole: "text"
                valueRole: "value"

                model: _root.action.conditionOperators
            }
        }

        Repeater {
            model: _root.action.conditions

            delegate: _conditionDelegate
            // delegate: _moreDelegation
        }

        // +-------------------------------------------------------------------
        // | True actions
        // +-------------------------------------------------------------------
        RowLayout {
            id: _trueHeader

            Label {
                text: "When the condition is <b>TRUE</b> then"
            }

            LayoutHorizontalSpacer {}

            ActionSelector {
                actionNode: _root.action
                callback: (x) => { _root.action.appendAction(x, "true"); }
            }
        }

        HorizontalDivider {
            id: _trueDivider

            Layout.fillWidth: true

            dividerColor: Style.lowColor
            lineWidth: 2
            spacing: 2
        }

        Repeater {
            model: _root.action.getActions("true")

            delegate: ActionNode {
                action: modelData
                parentAction: _root.action
                containerName: "true"

                Layout.fillWidth: true
            }
        }

        // +-------------------------------------------------------------------
        // | False actions
        // +-------------------------------------------------------------------
        RowLayout {
            id: _falseHeader

            Label {
                text: "When the condition is <b>FALSE</b> then"
            }

            LayoutHorizontalSpacer {}

            ActionSelector {
                actionNode: _root.action
                callback: (x) => { _root.action.appendAction(x, "false"); }
            }
        }

        HorizontalDivider {
            id: _falseDivider

            Layout.fillWidth: true

            dividerColor: Style.lowColor
            lineWidth: 2
            spacing: 2
        }

        Repeater {
            model: _root.action.getActions("false")

            delegate: ActionNode {
                action: modelData
                parentAction: _root.action
                containerName: "false"

                Layout.fillWidth: true
            }
        }
    }

    Component {
        id: _moreDelegation

        Item {
        Loader {
            active: modelData.conditionType === "vjoy"

            sourceComponent: RowLayout {
                Label {
                    Layout.preferredWidth: conditionLabelWidth
                    text: "vJoy Condition"
                }

                VJoySelector {
                    validTypes: ["axis", "button", "hat"]

                    onSelectionChanged: (vjoyId, inputType, inputId) => {
                        modelData.vjoyDeviceId = vjoyId
                        modelData.vJoyInputType = inputType
                        modelData.vjoyInputId = inputId
                    }

                    Component.onCompleted: () => {
                        initialize(
                            modelData.vjoyDeviceId,
                            modelData.vjoyInputType,
                            modelData.vjoyInputId
                        )
                    }
                }

                Label { text: "<b>True</b> when" }

                Comparator {
                    comparator: modelData.comparator
                }
            }
        }
        }
    }

    DelegateChooser {
        id: _conditionDelegate

        role: "conditionType"

        DelegateChoice {
            roleValue: "current_input"

            ConditionComponent {
                conditionItem: RowLayout {
                    Label {
                        Layout.preferredWidth: conditionLabelWidth

                        text: "Current Input"
                    }

                    Comparator {
                        comparator: modelData.comparator
                    }

                    LayoutHorizontalSpacer {}
                }
            }
        }

        DelegateChoice {
            roleValue: "joystick"

            ConditionComponent {
                conditionItem: RowLayout {
                    Label {
                        Layout.preferredWidth: conditionLabelWidth

                        text: "Joystick"
                    }

                    Label {
                        text: toUnorderedList(modelData.states)
                    }

                    Comparator {
                        comparator: modelData.comparator
                    }

                    LayoutHorizontalSpacer {}

                    InputListener {
                        callback: (inputs) => {
                            modelData.updateFromUserInput(inputs)
                        }
                        multipleInputs: true
                        eventTypes: ["axis", "button", "hat"]
                    }
                }
            }
        }

        DelegateChoice {
            roleValue: "keyboard"

            ConditionComponent {
                conditionItem: RowLayout {

                    Label {
                        Layout.preferredWidth: conditionLabelWidth

                        text: "Keyboard"
                    }

                    Label {
                        text: toUnorderedList(modelData.states)
                    }

                    Comparator {
                        comparator: modelData.comparator
                    }

                    LayoutHorizontalSpacer {}

                    InputListener {
                        callback: (inputs) => {
                            modelData.updateFromUserInput(inputs)
                        }
                        multipleInputs: true
                        eventTypes: ["key"]
                    }
                }
            }
        }

        DelegateChoice {
            roleValue: "logical_device"

            ConditionComponent {
                conditionItem: RowLayout {
                    Label {
                        Layout.preferredWidth: conditionLabelWidth
                        text: "Logical Device"
                    }

                    LogicalDeviceSelector {
                        // The ordering is important, swapping it will result in the
                        // wrong item being displayed.
                        validTypes: ["axis", "button", "hat"]
                        logicalInputIdentifier: modelData.logicalInputIdentifier

                        onLogicalInputIdentifierChanged: () => {
                            modelData.logicalInputIdentifier = logicalInputIdentifier
                        }
                    }

                    Label { text: "<b>True</b> when" }

                    Comparator {
                        comparator: modelData.comparator
                    }

                    LayoutHorizontalSpacer {}
                }
            }
        }

        DelegateChoice {
            roleValue: "vjoy"

            ConditionComponent {
                conditionItem: RowLayout {
                    Label {
                        Layout.preferredWidth: conditionLabelWidth
                        text: "vJoy Condition"
                    }

                    VJoySelector {
                        validTypes: ["axis", "button", "hat"]

                        onSelectionChanged: (vjoyId, inputType, inputId) => {
                            modelData.vjoyDeviceId = vjoyId
                            modelData.vJoyInputType = inputType
                            modelData.vjoyInputId = inputId
                        }

                        Component.onCompleted: () => {
                            initialize(
                                modelData.vjoyDeviceId,
                                modelData.vjoyInputType,
                                modelData.vjoyInputId
                            )
                        }
                    }

                    Label { text: "<b>True</b> when" }

                    Comparator {
                        comparator: modelData.comparator
                    }

                    LayoutHorizontalSpacer {}
                }
            }
        }
    }

    // Drop action for insertion into empty/first slot of the true actions
    ActionDragDropArea {
        target: _trueDivider
        dropCallback: (drop) => {
            modelData.dropAction(drop.text, modelData.sequenceIndex, "true");
        }
    }

    // Drop action for insertion into empty/first slot of the false actions
    ActionDragDropArea {
        target: _falseDivider
        dropCallback: (drop) => {
            modelData.dropAction(drop.text, modelData.sequenceIndex, "false");
        }
    }

    component DeleteConditionButton : IconButton {
        text: bsi.icons.remove
        font.pixelSize: 16

        onClicked: () => _root.action.removeCondition(index)
    }

    component ConditionComponent : RowLayout {
        property alias conditionItem: _actionLoader.sourceComponent

        Label {
            text: bsi.icons.bullet_point
            font.family: "bootstrap-icons"
            font.pixelSize: 24
        }

        // Contains the specific condition component.
        Loader {
            id: _actionLoader
            Layout.fillWidth: true
        }

        LayoutHorizontalSpacer {}

        Label {
            visible: modelData.isValid != true

            font.family: "bootstrap-icons"
            font.pixelSize: 24

            text: bsi.icons.error
            color: Style.error
        }

        DeleteConditionButton {}
    }
}
