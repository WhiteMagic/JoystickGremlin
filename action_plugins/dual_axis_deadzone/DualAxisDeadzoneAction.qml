// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Foundation
import Kobold.Composites

Item {
    id: _root

    required property DualAxisDeadzoneModel action

    property LabelValueSelectionModel deadzoneModel: action.deadzoneActionList
    property var _firstActions: action.getActions("first")
    property var _secondActions: action.getActions("second")

    implicitHeight: _content.height

    Connections {
        target: _root.action
        function onModelChanged() {
            _root.deadzoneModel.currentValue = _root.action.deadzone
            _root._firstActions = _root.action.getActions("first")
            _root._secondActions = _root.action.getActions("second")
        }
    }

    Dialog {
        id: _dialog
        anchors.centerIn: Overlay.overlay
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        focus: true
        title: "Rename action"

        TextField {
            id: _actionLabel
            focus: true
            text: _root.action.label
            placeholderText: "Action label"
            onAccepted: () => { _dialog.accept() }
        }

        onAccepted: () => { _root.action.label = _actionLabel.text }
    }

    ColumnLayout {
        id: _content
        anchors.left: parent.left
        anchors.right: parent.right

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
                onClicked: () => { _dialog.open() }
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
                valueLabel: _root.action.axis1.label
                isAssigned: _root.action.axis1.isValid
                onClicked: () => { _root.action.axis1 = uiState.currentInput }
            }

            Label { text: "Second axis" }
            InputAssignButton {
                valueLabel: _root.action.axis2.label
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

        Repeater {
            model: _root._firstActions

            delegate: ActionNode {
                required property var modelData
                required property int index

                Layout.fillWidth: true
                action: modelData
                previousSibling: index > 0 ? _root._firstActions[index - 1] : null
            }
        }

        SlotHeader {
            Layout.fillWidth: true
            label: "Second axis actions"
            actionNames: _root.action.compatibleActions
            onActionRequested: (name) => { _root.action.appendAction(name, "second") }
        }

        Repeater {
            model: _root._secondActions

            delegate: ActionNode {
                required property var modelData
                required property int index

                Layout.fillWidth: true
                action: modelData
                previousSibling: index > 0 ? _root._secondActions[index - 1] : null
            }
        }
    }
}
