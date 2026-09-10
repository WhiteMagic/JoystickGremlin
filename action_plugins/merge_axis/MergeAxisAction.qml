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

    required property MergeAxisModel action

    property LabelValueSelectionModel actionModel: action.mergeActionList
    property LabelValueSelectionModel operationModel: action.operationList

    implicitHeight: _content.height

    Connections {
        target: root.action
        function onModelChanged() {
            root.actionModel.currentValue = root.action.mergeAction
            root.operationModel.currentValue = root.action.operation
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
            Label {
                text: "Merge axis instance"
            }

            ComboBox {
                id: _actionSelection
                Layout.fillWidth: true
                model: root.actionModel
                textRole: "label"
                valueRole: "value"

                Component.onCompleted: () => {
                    currentIndex = root.actionModel.currentSelectionIndex
                }
                Connections {
                    target: root.actionModel
                    function onSelectionChanged() {
                        _actionSelection.currentIndex = root.actionModel.currentSelectionIndex
                    }
                }
                onActivated: () => {
                    root.actionModel.currentValue = currentValue
                    root.action.mergeAction = currentValue
                }
            }

            Button {
                text: "New instance"
                onClicked: () => { root.action.newMergeAxis() }
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
            Label {
                text: "Merge operation"
            }

            ComboBox {
                id: _operationSelection
                Layout.fillWidth: true
                model: root.operationModel
                textRole: "label"
                valueRole: "value"

                Component.onCompleted: () => {
                    currentIndex = root.operationModel.currentSelectionIndex
                }
                Connections {
                    target: root.operationModel
                    function onSelectionChanged() {
                        _operationSelection.currentIndex = root.operationModel.currentSelectionIndex
                    }
                }
                onActivated: () => {
                    root.operationModel.currentValue = currentValue
                    root.action.operation = currentValue
                }
            }
        }

        RowLayout {
            spacing: Metrics.gapL

            Label {
                text: "First axis"
            }

            InputAssignButton {
                valueLabel: root.action.firstAxis.isValid
                    ? root.action.firstAxis.label
                    : "Not assigned -- open the second axis and add this merge instance there to assign it."
                isAssigned: root.action.firstAxis.isValid
                onClicked: () => { root.action.firstAxis = uiState.currentInput }
            }

            Label {
                text: "Second axis"
            }

            InputAssignButton {
                valueLabel: root.action.secondAxis.isValid
                    ? root.action.secondAxis.label
                    : "Not assigned -- open the first axis and add this merge instance there to assign it."
                isAssigned: root.action.secondAxis.isValid
                onClicked: () => { root.action.secondAxis = uiState.currentInput }
            }
        }

        SlotHeader {
            Layout.fillWidth: true
            label: "Actions"
            actionNames: root.action.compatibleActions
            onActionRequested: (name) => { root.action.appendAction(name, "children") }
        }

        ActionList {
            Layout.fillWidth: true

            containerOwner: root.action
            containerName: "children"
        }
    }
}
