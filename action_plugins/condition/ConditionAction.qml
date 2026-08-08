// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.qmlmodels

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Composites
import Kobold.Foundation


// Body only -- no chevron, header, name field, guide or indent, those are the core's.
ColumnLayout {
    id: root

    required property ConditionModel action

    spacing: Metrics.gapM

    // +-------------------------------------------------------------------
    // | Logical condition setup
    // +-------------------------------------------------------------------
    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.gapM

        Label { text: "When" }

        ComboBox {
            id: _logicalOperatorSelector

            model: root.action.logicalOperators
            textRole: "text"
            valueRole: "value"

            Component.onCompleted: {
                currentIndex = indexOfValue(root.action.logicalOperator)
            }

            onActivated: { root.action.logicalOperator = currentValue }
        }

        Label { text: "of the following conditions are met" }

        Spacer {}

        ComboBox {
            id: _conditionType

            implicitContentWidthPolicy: ComboBox.WidestText
            textRole: "text"
            valueRole: "value"
            model: root.action.conditionOperators
        }

        Button {
            text: "Add condition"

            onClicked: { root.action.addCondition(_conditionType.currentValue) }
        }
    }

    Repeater {
        model: root.action.conditions

        delegate: _conditionDelegate
    }

    // +-------------------------------------------------------------------
    // | True actions
    // +-------------------------------------------------------------------
    SlotHeader {
        Layout.fillWidth: true

        label: "When true"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "true") }
    }

    ActionList {
        Layout.fillWidth: true

        containerOwner: root.action
        containerName: "true"
    }

    // +-------------------------------------------------------------------
    // | False actions
    // +-------------------------------------------------------------------
    SlotHeader {
        Layout.fillWidth: true

        label: "When false"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "false") }
    }

    ActionList {
        Layout.fillWidth: true

        containerOwner: root.action
        containerName: "false"
    }

    component DeleteConditionButton: ToolButton {
        icon.name: "delete"

        onClicked: () => { root.action.removeCondition(index) }
    }

    // Shared row shell for every condition type: an optional rule above (to separate
    // condition rows from one another -- this is a plain list, not an action container,
    // so SlotHeader's own rule does not apply here), the type-specific content in the
    // middle, and the error/delete controls at the end.
    component ConditionComponent: ColumnLayout {
        property alias conditionItem: _conditionLoader.sourceComponent
        property string conditionName: ""

        Layout.fillWidth: true

        Divider {
            Layout.fillWidth: true
            visible: index > 0
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.gapM

            Text {
                text: conditionName
                color: Theme.fgMuted
                font.family: FontType.sans
                font.pixelSize: Metrics.textDetail
            }

            Loader {
                id: _conditionLoader

                Layout.fillWidth: true
            }

            Spacer {}

            AppIcon {
                visible: modelData.isValid !== true
                name: "error"
                role: "error"

                HoverHandler {
                    id: _conditionErrorHover
                }

                ToolTip.visible: _conditionErrorHover.hovered
                ToolTip.text: "This condition has not been fully configured yet."
            }

            DeleteConditionButton {}
        }
    }

    DelegateChooser {
        id: _conditionDelegate

        role: "conditionType"

        DelegateChoice {
            roleValue: "current_input"

            ConditionComponent {
                conditionName: "Current input"

                conditionItem: RowLayout {
                    spacing: Metrics.gapM

                    Comparator {
                        comparator: modelData.comparator
                    }
                }
            }
        }

        DelegateChoice {
            roleValue: "joystick"

            ConditionComponent {
                conditionName: "Joystick"

                conditionItem: RowLayout {
                    spacing: Metrics.gapM

                    InputCaptureButton {
                        eventTypes: ["axis", "button", "hat"]
                        multipleInputs: true
                        text: modelData.states.length > 0 ?
                            modelData.states.join(", ") : "Record inputs"

                        callback: (inputs) => { modelData.updateFromUserInput(inputs) }
                    }

                    Comparator {
                        comparator: modelData.comparator
                    }
                }
            }
        }

        DelegateChoice {
            roleValue: "keyboard"

            ConditionComponent {
                conditionName: "Keyboard"

                conditionItem: RowLayout {
                    spacing: Metrics.gapM

                    InputCaptureButton {
                        eventTypes: ["key"]
                        multipleInputs: true
                        text: modelData.states.length > 0 ?
                            modelData.states.join(", ") : "Record keys"

                        callback: (inputs) => { modelData.updateFromUserInput(inputs) }
                    }

                    Comparator {
                        comparator: modelData.comparator
                    }
                }
            }
        }

        DelegateChoice {
            roleValue: "logical_device"

            ConditionComponent {
                conditionName: "Logical device"

                conditionItem: RowLayout {
                    spacing: Metrics.gapM

                    LogicalDeviceSelector {
                        validTypes: ["axis", "button", "hat"]
                        logicalInputIdentifier: modelData.logicalInputIdentifier

                        onLogicalInputIdentifierChanged: {
                            modelData.logicalInputIdentifier = logicalInputIdentifier
                        }
                    }

                    Label { text: "True when" }

                    Comparator {
                        comparator: modelData.comparator
                    }
                }
            }
        }

        DelegateChoice {
            roleValue: "vjoy"

            ConditionComponent {
                conditionName: "vJoy"

                conditionItem: RowLayout {
                    spacing: Metrics.gapM

                    VJoySelector {
                        validTypes: ["axis", "button", "hat"]

                        onSelectionChanged: (vjoyId, inputType, inputId) => {
                            modelData.vjoyDeviceId = vjoyId
                            modelData.vjoyInputType = inputType
                            modelData.vjoyInputId = inputId
                        }

                        Component.onCompleted: {
                            initialize(
                                modelData.vjoyDeviceId,
                                modelData.vjoyInputType,
                                modelData.vjoyInputId
                            )
                        }
                    }

                    Label { text: "True when" }

                    Comparator {
                        comparator: modelData.comparator
                    }
                }
            }
        }
    }
}
