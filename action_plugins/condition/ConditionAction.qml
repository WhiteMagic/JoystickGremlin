// -*- coding: utf-8; -*-
//
// Copyright (C) 2020 Lionel Ott
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

                Component.onCompleted: () => {
                    currentIndex = indexOfValue(_root.action.logicalOperator)
                }

                onActivated: () => {
                    _root.action.logicalOperator = currentValue
                }
            }
            Label {
                text: "of the following conditions are met"
            }

            LayoutHorizontalSpacer {}

            Button {
                text: "Add Condition"

                onClicked: () => {
                    _root.action.addCondition(_condition.currentValue)
                }
            }

            ComboBox {
                id: _condition

                implicitContentWidthPolicy: ComboBox.WidestText
                textRole: "text"
                valueRole: "value"

                model: _root.action.conditionOperators
            }
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
                    text: bsi.icons.trash
                    Layout.alignment: Qt.AlignTop
                    Layout.topMargin: 4

                    onClicked: () => {
                        _root.action.removeCondition(conditionIndex)
                    }
                }
            }
        }

        // +-------------------------------------------------------------------
        // | True actions
        // +-------------------------------------------------------------------
        RowLayout {
            id: _trueHeader

            Label {
                text: "When the condition is <b>TRUE</b> then"
            }

            LayoutHorizontalSpacer {}

            ActionSelector {
                actionNode: _root.action
                callback: (x) => { _root.action.appendAction(x, "true"); }
            }
        }

        HorizontalDivider {
            id: _trueDivider

            Layout.fillWidth: true

            dividerColor: Universal.baseLowColor
            lineWidth: 2
            spacing: 2
        }

        Repeater {
            model: _root.action.getActions("true")

            delegate: ActionNode {
                action: modelData
                parentAction: _root.action
                containerName: "true"

                Layout.fillWidth: true
            }
        }

        // +-------------------------------------------------------------------
        // | False actions
        // +-------------------------------------------------------------------
        RowLayout {
            id: _falseHeader

            Label {
                text: "When the condition is <b>FALSE</b> then"
            }

            LayoutHorizontalSpacer {}

            ActionSelector {
                actionNode: _root.action
                callback: (x) => { _root.action.appendAction(x, "false"); }
            }
        }

        HorizontalDivider {
            id: _falseDivider

            Layout.fillWidth: true

            dividerColor: Universal.baseLowColor
            lineWidth: 2
            spacing: 2
        }

        Repeater {
            model: _root.action.getActions("false")

            delegate: ActionNode {
                action: modelData
                parentAction: _root.action
                containerName: "false"

                Layout.fillWidth: true
            }
        }
    }

    // Drop action for insertion into empty/first slot of the true actions
    ActionDragDropArea {
        target: _trueDivider
        dropCallback: (drop) => {
            modelData.dropAction(drop.text, modelData.sequenceIndex, "true");
        }
    }

    // Drop action for insertion into empty/first slot of the false actions
    ActionDragDropArea {
        target: _falseDivider
        dropCallback: (drop) => {
            modelData.dropAction(drop.text, modelData.sequenceIndex, "false");
        }
    }
}