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
import QtQuick.Controls.Universal
import QtQuick.Layouts
import QtQuick.Window

import QtQuick.Controls.Universal

import Gremlin.Profile
import Gremlin.ActionPlugins
import "../../qml"


Item {
    id: _root

    property ActionNodeModel node
    property ConditionModel action

    implicitHeight: _content.height

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

                Component.onCompleted: {
                    currentIndex = indexOfValue(_root.action.logicalOperator)
                }

                onActivated: {
                    _root.action.logicalOperator = currentValue
                }
            }
            Label {
                text: "of the following conditions are met"
            }

            Rectangle {
                Layout.fillWidth: true
            }

            Button {
                text: "Add Condition"

                onClicked: {
                    _root.action.addCondition(_condition.currentValue)
                }
            }

            ComboBox {
                id: _condition

                textRole: "text"
                valueRole: "value"

                model: _root.action.conditionOperators
            }
        }

        Rectangle {
            Layout.fillWidth: true

            height: 2
            color: Universal.accent
        }

        Repeater {
            model: _root.action.conditions

            delegate: RowLayout {
                property int conditionIndex: index

                ConditionComparatorUI {
                    Layout.fillWidth: true

                    model: modelData
                }
                IconButton {
                    Layout.alignment: Qt.AlignTop
                    Layout.topMargin: 4

                    text: "\uf2ed"

                    onClicked: function()
                    {
                        console.log("Deleting :" + conditionIndex)
                        _root.action.removeCondition(conditionIndex)
                    }
                }
            }
        }

        // +-------------------------------------------------------------------
        // | True actions
        // +-------------------------------------------------------------------
        RowLayout {
            Label {
                text: "Condition is <b>true</b>"
            }

            Rectangle {
                Layout.fillWidth: true
            }

            ActionSelector {
                actionNode: _root.node
                callback: function(x) { _root.action.addAction(x, "if"); }
            }
        }

        Rectangle {
            id: _trueDivider
            Layout.fillWidth: true
            height: 2
            color: "green"
        }

        Repeater {
            model: _root.action.trueActionNodes

            delegate: ActionNode {
                action: modelData

                Layout.fillWidth: true
            }
        }

        // +-------------------------------------------------------------------
        // | False actions
        // +-------------------------------------------------------------------
        RowLayout {
            Label {
                text: "Condition is <b>false</b>"
            }

            Rectangle {
                Layout.fillWidth: true
            }

            ActionSelector {
                actionNode: _root.node
                callback: function(x) { _root.action.addAction(x, "else"); }
            }
        }

        Rectangle {
            id: _falseDivider
            Layout.fillWidth: true
            height: 2
            color: "red"
        }

        Repeater {
            model: _root.action.falseActionNodes

            delegate: ActionNode {
                action: modelData

                Layout.fillWidth: true
            }
        }

        // Bottom spacer
        Rectangle {
            Layout.fillWidth: true
            height: 10
            color: "transparent"
        }
    }

    // Drop action for insertion into empty/first slot of the true actions
    DropArea {
        x: _trueDivider.x
        y: _trueDivider.y
        width: _trueDivider.width
        height: 30

        // Visualization of the drop indicator
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top

            height: 5

            opacity: parent.containsDrag ? 1.0 : 0.0
            color: Universal.accent
        }

        onDropped: function(drop)
        {
            if(drop.text != _root.action.id)
            {
                drop.accept();
                modelData.dropAction(drop.text, modelData.id, "true");
            }
        }
    }

    // Drop action for insertion into empty/first slot of the false actions
    DropArea {
        x: _falseDivider.x
        y: _falseDivider.y
        width: _falseDivider.width
        height: 30

        // Visualization of the drop indicator
        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top

            height: 5

            opacity: parent.containsDrag ? 1.0 : 0.0
            color: Universal.accent
        }

        onDropped: function(drop)
        {
            if(drop.text != _root.action.id)
            {
                drop.accept();
                modelData.dropAction(drop.text, modelData.id, "false");
            }
        }
    }
}