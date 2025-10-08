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
import QtQuick.Controls.Universal
import QtQuick.Layouts
import QtQuick.Window

import QtQuick.Controls.Universal

import Gremlin.Profile
import Gremlin.ActionPlugins
import "../../qml"


Item {
    id: _root

    property SplitAxisModel action

    implicitHeight: _content.height

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        RowLayout {
            Label {
                text: "Split axis at"
            }

            FloatSpinBox {
                minValue: -1.0
                maxValue: 1.0
                value: _root.action.splitValue
                stepSize: 0.05

                onValueModified: (newValue) => {
                    _root.action.splitValue = newValue
                }
            }
        }

        // +-------------------------------------------------------------------
        // | Upper split actions
        // +-------------------------------------------------------------------
        RowLayout {
            id: _upperHeader

            Label {
                text: "Actions for the <b>upper</b> part of the split."
            }

            Rectangle {
                Layout.fillWidth: true
            }

            ActionSelector {
                actionNode: _root.action
                callback: (x) => { _root.action.appendAction(x, "upper"); }
            }
        }

        HorizontalDivider {
            id: _upperDivider

            Layout.fillWidth: true

            dividerColor: Universal.baseLowColor
            lineWidth: 2
            spacing: 2
        }

        Repeater {
            model: _root.action.getActions("upper")

            delegate: ActionNode {
                action: modelData
                parentAction: _root.action
                containerName: "upper"

                Layout.fillWidth: true
            }
        }

        // +-------------------------------------------------------------------
        // | Lower split actions
        // +-------------------------------------------------------------------
        RowLayout {
            id: _lowerHeader

            Label {
                text: "Actions for the <b>lower</b> part of the split."
            }

            Rectangle {
                Layout.fillWidth: true
            }

            ActionSelector {
                actionNode: _root.action
                callback: (x) => { _root.action.appendAction(x, "lower"); }
            }
        }

        HorizontalDivider {
            id: _lowerDivider

            Layout.fillWidth: true

            dividerColor: Universal.baseLowColor
            lineWidth: 2
            spacing: 2
        }

        Repeater {
            model: _root.action.getActions("lower")

            delegate: ActionNode {
                action: modelData
                parentAction: _root.action
                containerName: "lower"

                Layout.fillWidth: true
            }
        }
    }

    // Drop action for insertion into empty/first slot of the upper actions
    ActionDragDropArea {
        target: _upperDivider
        dropCallback: (drop) => {
            console.log("Dropped", drop.text, "on upper divider" + modelData.id);
            modelData.dropAction(drop.text, modelData.sequenceIndex, "upper");
        }
    }

    // Drop action for insertion into empty/first slot of the lower actions
    ActionDragDropArea {
        target: _lowerDivider
        dropCallback: (drop) => {
            modelData.dropAction(drop.text, modelData.sequenceIndex, "lower");
        }
    }

}