// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2022 Lionel Ott
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
import Gremlin.ActionPlugins
import "../../qml"


Item {
    id: _root

    property MergeAxisModel action

    property LabelValueSelectionModel model: action.mergeActionList

    implicitHeight: _content.height

    Connections {
        target: action

        function onModelChanged()
        {
            model.currentValue = _root.action.mergeAction
        }
    }

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
                id: _action_label

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
            action.label = _action_label.text
        }
    }

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        // Display the configuration options for the merging operation
        GridLayout {
            rows: 4
            columns: 3

            // Row 1
            Label {
                text: "Action"
            }
            LabelValueComboBox
            {
                id: _action_selection

                model: _root.model

                Component.onCompleted: function()
                {
                    _root.model.currentValue = _root.action.mergeAction
                }


                onSelectionChanged: function()
                {
                    _root.action.mergeAction = _root.model.currentValue
                }
            }

            Row {
                IconButton {
                    text: bsi.icons.add_new
                    font.pixelSize: 24

                    onClicked: function () {
                        _root.action.newMergeAxis()
                    }
                }

                IconButton {
                    text: bsi.icons.rename
                    font.pixelSize: 24

                    onClicked: function () {
                        _dialog.open()
                    }
                }
            }

            // Row 2
            Label {
                text: "First axis"
            }
            Label {
                text: _root.action.firstAxis.label
            }
            IconButton {
                text: bsi.icons.replace

                onClicked: function()
                {
                    _root.action.firstAxis = inputIdentifier
                }
            }

            // Row 3
            Label {
                text: "Second axis"
            }
            Label {
                text: _root.action.secondAxis.label
            }
            IconButton {
                text: bsi.icons.replace

                onClicked: function()
                {
                    _root.action.secondAxis = inputIdentifier
                }
            }

            // Row 4
            Label {
                text: "Merge operation"
            }
            ComboBox {
                model: _root.action.operationList
                Layout.columnSpan: 2
            }
        }


        // Display the actions operating on the merged axis output
        ListView {
            model: _root.action.getActions("children")

            delegate: ActionNode {
                action: modelData
                parentAction: _root.action
                containerName: "children"

                Layout.fillWidth: true
            }
        }
    }
}