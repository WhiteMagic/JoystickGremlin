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
import QtQuick.Layouts
import QtQuick.Window

import QtQuick.Controls.Universal

import Gremlin.Profile
import Gremlin.UI
import Gremlin.ActionPlugins
import "../../qml"


Item {
    id: _root

    property DualAxisDeadzoneModel action
    property LabelValueSelectionModel deadzoneListModel: action.deadzoneActionList

    implicitHeight: _content.height

    Connections {
        target: action

        function onModelChanged()
        {
            deadzoneListModel.currentValue = _root.action.deadzone
        }
    }


    // Dialog to change the label of the current action
    Dialog {
        id: _dialog

        anchors.centerIn: Overlay.overlay

        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true
        focus: true

        title: "Rename action"

        Row
        {
            anchors.fill: parent

            TextField {
                id: _actionLabel

                width: 400
                focus: true

                text: action.label
                placeholderText: "Action label"

                onAccepted: function()
                {
                    _dialog.accept()
                }
            }
        }

        onAccepted: function()
        {
            action.label = _actionLabel.text
        }
    }


    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        // +-------------------------------------------------------------------
        // | Deadzone instance selection and management
        // +-------------------------------------------------------------------
        RowLayout {
            Label {
                text: "Deadzone instance"
            }
            LabelValueComboBox {
                model: _root.deadzoneListModel

                Component.onCompleted: function () {
                    _root.deadzoneListModel.currentValue = _root.action.deadzone
                }

                onSelectionChanged: function () {
                    _root.action.deadzone = _root.deadzoneListModel.currentValue
                }
            }

            IconButton {
                text: bsi.icons.add_new
                font.pixelSize: 24

                onClicked: () => _root.action.newDeadzone()
            }

            IconButton {
                text: bsi.icons.rename
                font.pixelSize: 24

                onClicked: () => _dialog.open()
            }

            LayoutHorizontalSpacer {}

            // Deadzone configuration
            RowLayout {
                Text {
                    text: "Deadzone limits: "
                }

                Text {
                    text: "Inner"
                }

                FloatSpinBox {
                    id: _innerValue

                    value: _root.action.innerDeadzone
                    minValue: 0.0
                    maxValue: 1.0

                    onValueModified: (newValue) => {
                        _root.action.innerDeadzone = newValue
                    }
                }

                Text {
                    text: "Outer"
                }

                FloatSpinBox {
                    id: _outerValue

                    value: _root.action.outerDeadzone
                    minValue: 0.0
                    maxValue: 1.0

                    onValueModified: (newValue) => {
                        _root.action.outerDeadzone = newValue

                    }
                }
            }
        }


        // +-------------------------------------------------------------------
        // | Axis assignments
        // +-------------------------------------------------------------------
        RowLayout {
            // First axis selection
            Label {
                text: "First axis: "
                font.family: "Segoe UI"
                font.weight: 600
            }
            Label {
                text: _root.action.axis1.label
            }
            IconButton {
                text: bsi.icons.replace

                onClicked: function () {
                    _root.action.axis1 = uiState.currentInput
                }
            }

            LayoutHorizontalSpacer {
                Layout.fillWidth: false
                Layout.preferredWidth: 50
            }

            // Second axis selection
            Label {
                text: "Second axis: "
                font.family: "Segoe UI"
                font.weight: 600
            }
            Label {
                text: _root.action.axis2.label
            }
            IconButton {
                text: bsi.icons.replace

                onClicked: function () {
                    _root.action.axis2 = uiState.currentInput
                }
            }
        }


        // +-------------------------------------------------------------------
        // | First axis actions
        // +-------------------------------------------------------------------
        RowLayout {
            Label {
                text: "First axis"
            }

            Rectangle {
                Layout.fillWidth: true
            }

            ActionSelector {
                actionNode: _root.action
                callback: (x) => _root.action.appendAction(x, "first")
            }
        }

        Rectangle {
            id: _firstDivider
            Layout.fillWidth: true
            height: 2
            color: Universal.baseLowColor
        }

        Repeater {
            model: _root.action.getActions("first")

            delegate: ActionNode {
                action: modelData
                parentAction: _root.action
                containerName: "first"

                Layout.fillWidth: true
            }
        }

        // +-------------------------------------------------------------------
        // | Second axis actions
        // +-------------------------------------------------------------------
        RowLayout {
            Label {
                text: "Second axis"
            }

            Rectangle {
                Layout.fillWidth: true
            }

            ActionSelector {
                actionNode: _root.action
                callback: (x) => _root.action.appendAction(x, "second")
            }
        }

        Rectangle {
            id: _secondDivider
            Layout.fillWidth: true
            height: 2
            color: Universal.baseLowColor
        }

        Repeater {
            model: _root.action.getActions("second")

            delegate: ActionNode {
                action: modelData
                parentAction: _root.action
                containerName: "second"

                Layout.fillWidth: true
            }
        }
    }

    // Drop action for insertion into empty/first slot of the short actions
    ActionDragDropArea {
        target: _firstDivider
        dropCallback: function(drop) {
            modelData.dropAction(drop.text, modelData.sequenceIndex, "first");
        }
    }

    // Drop action for insertion into empty/first slot of the long actions
    ActionDragDropArea {
        target: _secondDivider
        dropCallback: function(drop) {
            modelData.dropAction(drop.text, modelData.sequenceIndex, "second");
        }
    }
}