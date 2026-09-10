// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Foundation
import Kobold.Composites


Item {
    id: root

    required property DualAxisDeadzoneModel action

    property LabelValueSelectionModel deadzoneModel: action.deadzoneActionList

    implicitHeight: _content.height

    Connections {
        target: root.action
        function onModelChanged() {
            root.deadzoneModel.currentValue = root.action.deadzone
        }
    }

    TextInputDialog {
        id: _renameDialog

        visible: false
        title: "Rename action"

        onAccepted: (value) => {
            root.action.label = value
            visible = false
        }
    }

    ColumnLayout {
        id: _content
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: Metrics.gapM

        RowLayout {
            Label { text: "Deadzone instance" }

            ComboBox {
                id: _deadzoneSelection
                Layout.fillWidth: true
                model: root.deadzoneModel
                textRole: "label"
                valueRole: "value"

                Component.onCompleted: () => {
                    currentIndex = root.deadzoneModel.currentSelectionIndex
                }
                Connections {
                    target: root.deadzoneModel
                    function onSelectionChanged() {
                        _deadzoneSelection.currentIndex =
                            root.deadzoneModel.currentSelectionIndex
                    }
                }
                onActivated: () => {
                    root.deadzoneModel.currentValue = currentValue
                    root.action.deadzone = currentValue
                }
            }

            Button {
                text: "New instance"
                onClicked: () => { root.action.newDeadzone() }
            }

            ToolButton {
                icon.name: "edit"
                onClicked: () => {
                    _renameDialog.text = root.action.label
                    _renameDialog.visible = true
                }
            }
        }

        RowLayout {
            spacing: Metrics.gapL

            Label {
                text: "Inner deadzone"
            }

            DoubleSpinBox {
                from: 0.0
                to: 1.0
                stepSize: 0.05
                decimals: Metrics.preciseDecimalPlaces
                value: root.action.innerDeadzone

                onValueModified: { root.action.innerDeadzone = value }
            }

            Label {
                text: "Outer deadzone"
            }

            DoubleSpinBox {
                from: 0.0
                to: 1.0
                stepSize: 0.05
                decimals: Metrics.preciseDecimalPlaces
                value: root.action.outerDeadzone

                onValueModified: { root.action.outerDeadzone = value }
            }
        }

        RowLayout {
            spacing: Metrics.gapL

            Label {
                text: "First axis"
            }

            InputAssignButton {
                valueLabel: root.action.axis1.isValid
                    ? root.action.axis1.label
                    : "Not assigned"
                isAssigned: root.action.axis1.isValid
                onClicked: () => { root.action.axis1 = uiState.currentInput }
            }

            Label {
                text: "Second axis"
            }

            InputAssignButton {
                valueLabel: root.action.axis2.isValid
                    ? root.action.axis2.label
                    : "Not assigned"
                isAssigned: root.action.axis2.isValid
                onClicked: () => { root.action.axis2 = uiState.currentInput }
            }
        }

        SlotHeader {
            Layout.fillWidth: true
            label: "First axis actions"
            actionNames: root.action.compatibleActions
            onActionRequested: (name) => { root.action.appendAction(name, "first") }
        }

        ActionList {
            Layout.fillWidth: true

            containerOwner: root.action
            containerName: "first"
        }

        SlotHeader {
            Layout.fillWidth: true
            label: "Second axis actions"
            actionNames: root.action.compatibleActions
            onActionRequested: (name) => { root.action.appendAction(name, "second") }
        }

        ActionList {
            Layout.fillWidth: true

            containerOwner: root.action
            containerName: "second"
        }
    }
}
