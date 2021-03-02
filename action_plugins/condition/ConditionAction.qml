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

        Row {
            id: _logicalOperator

            spacing: 10

            Label {
                anchors.verticalCenter: _logicalOperator.verticalCenter

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
                anchors.verticalCenter: _logicalOperator.verticalCenter

                text: "of the following conditions are met"
            }
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

        Row {
            id: _conditionTypes

            spacing: 10

            ComboBox {
                id: _condition

                textRole: "text"
                valueRole: "value"

                model: _root.action.conditionOperators
            }
            Button {
                text: "Add Condition"

                onClicked: {
                    _root.action.addCondition(_condition.currentValue)
                }
            }
        }

        Label {
            id: _labelThen

            text: "Then"
        }

        Repeater {
            model: _root.action.trueActionNodes

            delegate: ActionNode {
                action: modelData

                Layout.fillWidth: true
            }
        }

        Label {
            id: _labelElse

            text: "Else"
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