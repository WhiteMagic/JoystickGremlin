// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2021 Lionel Ott
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

    property ActionNodeModel node
    property TempoModel action

    implicitHeight: _content.height

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        // +-------------------------------------------------------------------
        // | Behavior configuration
        // +-------------------------------------------------------------------
        RowLayout {
            Label {
                id: _label

                text: "Long-press threshold (sec)"
            }
            FloatSpinBox {
                minValue: 0
                maxValue: 100
                value: _root.action.threshold
                stepSize: 0.05

                onValueChanged: {
                    _root.action.threshold = value
                }
            }

            LayoutSpacer {}

            Label {
                text: "Activate on"
            }
            RadioButton {
                text: "press"
                checked: _root.action.activateOn == "press"
                
                onClicked: {
                    _root.action.activateOn = "press"
                }
            }
            RadioButton {
                text: "release"
                checked: _root.action.activateOn == "release"

                onClicked: {
                    _root.action.activateOn = "release"
                }
            }
        }

        // +-------------------------------------------------------------------
        // | Short press actions
        // +-------------------------------------------------------------------
        RowLayout {
            Label {
                text: "Short press"
            }

            Rectangle {
                Layout.fillWidth: true
            }

            ActionSelector {
                actionNode: _root.node
                callback: function(x) { _root.action.addAction(x, "short"); }
            }
        }

        Rectangle {
            id: _shortDivider
            Layout.fillWidth: true
            height: 2
            color: Universal.baseLowColor
        }

        Repeater {
            model: _root.action.shortActions

            delegate: ActionNode {
                action: modelData

                Layout.fillWidth: true
            }
        }

        // +-------------------------------------------------------------------
        // | Long press actions
        // +-------------------------------------------------------------------
        RowLayout {
            Label {
                text: "Long press"
            }

            Rectangle {
                Layout.fillWidth: true
            }

            ActionSelector {
                actionNode: _root.node
                callback: function(x) { _root.action.addAction(x, "long"); }
            }
        }

        Rectangle {
            id: _longDivider
            Layout.fillWidth: true
            height: 2
            color: Universal.baseLowColor
        }

        Repeater {
            model: _root.action.longActions

            delegate: ActionNode {
                action: modelData

                Layout.fillWidth: true
            }
        }

        // Bottom spacer
        Rectangle {
            Layout.fillWidth: true
            height: 10
        }
    }

    // Drop action for insertion into empty/first slot of the short actions
    DropArea {
        x: _shortDivider.x
        y: _shortDivider.y
        width: _shortDivider.width
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
                modelData.dropAction(drop.text, modelData.id, "short");
            }
        }
    }

    // Drop action for insertion into empty/first slot of the long actions
    DropArea {
        x: _longDivider.x
        y: _longDivider.y
        width: _longDivider.width
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
                modelData.dropAction(drop.text, modelData.id, "long");
            }
        }
    }
}