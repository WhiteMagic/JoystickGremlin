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
    id: _root

    required property DualAxisDeadzoneModel action

    property LabelValueSelectionModel deadzoneModel: action.deadzoneActionList

    implicitHeight: _content.height

    Connections {
        target: _root.action
        function onModelChanged() {
            _root.deadzoneModel.currentValue = _root.action.deadzone
        }
    }

    TextInputDialog {
        id: _renameDialog

        visible: false
        title: "Rename action"

        onAccepted: (value) => {
            _root.action.label = value
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
                model: _root.deadzoneModel
                textRole: "label"
                valueRole: "value"

                Component.onCompleted: () => {
                    currentIndex = _root.deadzoneModel.currentSelectionIndex
                }
                Connections {
                    target: _root.deadzoneModel
                    function onSelectionChanged() {
                        _deadzoneSelection.currentIndex = _root.deadzoneModel.currentSelectionIndex
                    }
                }
                onActivated: () => {
                    _root.deadzoneModel.currentValue = currentValue
                    _root.action.deadzone = currentValue
                }
            }

            Button {
                text: "New instance"
                onClicked: () => { _root.action.newDeadzone() }
            }
            ToolButton {
                icon.name: "edit"
                onClicked: () => {
                    _renameDialog.text = _root.action.label
                    _renameDialog.visible = true
                }
            }
        }

        RowLayout {
            spacing: Metrics.gapL

            Label { text: "Inner deadzone" }

            DoubleSpinBox {
                from: 0.0
                to: 1.0
                stepSize: 0.05
                decimals: 4
                value: _root.action.innerDeadzone

                onValueModified: { _root.action.innerDeadzone = value }
            }

            Label { text: "Outer deadzone" }

            DoubleSpinBox {
                from: 0.0
                to: 1.0
                stepSize: 0.05
                decimals: 4
                value: _root.action.outerDeadzone

                onValueModified: { _root.action.outerDeadzone = value }
            }
        }

        RowLayout {
            spacing: Metrics.gapL

            Label { text: "First axis" }
            InputAssignButton {
                valueLabel: _root.action.axis1.isValid
                    ? _root.action.axis1.label
                    : "Not assigned -- open the second axis and add this dual axis deadzone instance there to assign it."
                isAssigned: _root.action.axis1.isValid
                onClicked: () => { _root.action.axis1 = uiState.currentInput }
            }

            Label { text: "Second axis" }
            InputAssignButton {
                valueLabel: _root.action.axis2.isValid
                    ? _root.action.axis2.label
                    : "Not assigned -- open the first axis and add this dual axis deadzone instance there to assign it."
                isAssigned: _root.action.axis2.isValid
                onClicked: () => { _root.action.axis2 = uiState.currentInput }
            }
        }

        SlotHeader {
            Layout.fillWidth: true
            label: "First axis actions"
            actionNames: _root.action.compatibleActions
            onActionRequested: (name) => { _root.action.appendAction(name, "first") }
        }

        ActionList {
            Layout.fillWidth: true

            containerOwner: _root.action
            containerName: "first"
        }

        SlotHeader {
            Layout.fillWidth: true
            label: "Second axis actions"
            actionNames: _root.action.compatibleActions
            onActionRequested: (name) => { _root.action.appendAction(name, "second") }
        }

        ActionList {
            Layout.fillWidth: true

            containerOwner: _root.action
            containerName: "second"
        }
    }
}
