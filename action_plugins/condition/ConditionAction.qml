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

    property ActionTreeModel actionTree
    property ConditionModel model

    //height: _layout.height
    //width: parent.width

    ColumnLayout {
        id: _layout

        Row {
            id: _logicalOperator

            spacing: 10

            Label {
                anchors.verticalCenter: _logicalOperator.verticalCenter

                text: "If "
            }
            ComboBox {
                id: _logicalOperatorSelector
                model: ["any", "all"]
            }
            Label {
                anchors.verticalCenter: _logicalOperator.verticalCenter

                text: "of the following conditions are met"
            }
        }

        ListView {
            id: _conditionList

            height: childrenRect.height

            model: ["1", "2", "3"]

            delegate: Label {
                text: modelData
            }
        }

        Row {
            id: _conditionTypes

            spacing: 10

            ComboBox {
                model: ["A", "B", "C"]
            }
            Button {
                text: "Add Condition"
            }
        }

        Label {
            id: _labelThen

            text: "Then"
        }

        Repeater {
            id: _actionThen

            model: _root.model.trueActionNodes

            delegate: ActionNode {
                id: _action

                action: modelData
                actionTree: _root.actionTree
            }
        }

        Label {
            id: _labelElse

            text: "Else"
        }

        Repeater {
            id: _actionElse

            model: _root.model.trueActionNodes

            delegate: ActionNode {
                id: _action

                action: modelData
                actionTree: _root.actionTree
            }
        }

    }
}