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

    required property MergeAxisModel action

    property LabelValueSelectionModel actionModel: action.mergeActionList
    property LabelValueSelectionModel operationModel: action.operationList
    property var _childActions: action.getActions("children")

    implicitHeight: _content.height

    Connections {
        target: _root.action
        function onModelChanged() {
            _root.actionModel.currentValue = _root.action.mergeAction
            _root.operationModel.currentValue = _root.action.operation
            _root._childActions = _root.action.getActions("children")
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
            Label { text: "Merge axis instance" }

            ComboBox {
                id: _actionSelection
                Layout.fillWidth: true
                model: _root.actionModel
                textRole: "label"
                valueRole: "value"

                Component.onCompleted: () => {
                    currentIndex = _root.actionModel.currentSelectionIndex
                }
                Connections {
                    target: _root.actionModel
                    function onSelectionChanged() {
                        _actionSelection.currentIndex = _root.actionModel.currentSelectionIndex
                    }
                }
                onActivated: () => {
                    _root.actionModel.currentValue = currentValue
                    _root.action.mergeAction = currentValue
                }
            }

            Button {
                text: "New instance"
                onClicked: () => { _root.action.newMergeAxis() }
            }
            ToolButton {
                icon.name: "edit"
                onClicked: () => { _dialog.open() }
            }
        }

        RowLayout {
            Label { text: "Merge operation" }

            ComboBox {
                id: _operationSelection
                Layout.fillWidth: true
                model: _root.operationModel
                textRole: "label"
                valueRole: "value"

                Component.onCompleted: () => {
                    currentIndex = _root.operationModel.currentSelectionIndex
                }
                Connections {
                    target: _root.operationModel
                    function onSelectionChanged() {
                        _operationSelection.currentIndex = _root.operationModel.currentSelectionIndex
                    }
                }
                onActivated: () => {
                    _root.operationModel.currentValue = currentValue
                    _root.action.operation = currentValue
                }
            }
        }

        RowLayout {
            spacing: Metrics.gapL

            Label { text: "First axis" }
            InputAssignButton {
                valueLabel: _root.action.firstAxis.label
                isAssigned: _root.action.firstAxis.isValid
                onClicked: () => { _root.action.firstAxis = uiState.currentInput }
            }

            Label { text: "Second axis" }
            InputAssignButton {
                valueLabel: _root.action.secondAxis.label
                isAssigned: _root.action.secondAxis.isValid
                onClicked: () => { _root.action.secondAxis = uiState.currentInput }
            }
        }

        SlotHeader {
            Layout.fillWidth: true
            label: "Actions"
            actionNames: _root.action.compatibleActions
            onActionRequested: (name) => { _root.action.appendAction(name, "children") }
        }

        Repeater {
            model: _root._childActions

            delegate: ActionNode {
                required property var modelData
                required property int index

                Layout.fillWidth: true
                action: modelData
                previousSibling: index > 0 ? _root._childActions[index - 1] : null
            }
        }
    }
}
