// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2020 Lionel Ott
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

import QtQuick 2.14
import QtQuick.Controls 2.14
import QtQuick.Controls.Universal 2.14
import QtQuick.Layouts 1.14
import QtQuick.Window 2.14

import QtQuick.Controls.Universal 2.14

import gremlin.ui.profile 1.0
import gremlin.plugins 1.0
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
                ConditionComparator {
                    model: modelData

                    Layout.fillWidth: true
                }
                IconButton {
                    text: "\uf2ed"

                    onClicked: {
                        _root.action.removeCondition(index)
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
    }
}