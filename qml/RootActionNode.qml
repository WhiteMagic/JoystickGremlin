// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2023 Lionel Ott
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

import Gremlin.ActionPlugins
import Gremlin.Profile



Item {
    id: _root

    // Data to render
    property RootModel action

    implicitHeight: _content.height


    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        Rectangle {
            id: _topRule

            Layout.fillWidth: true
            height: 0
            color: "transparent"
        }

        Repeater {
            model: _root.action.getActions("children")

            delegate: ActionNode {
                action: modelData
                parentAction: _root.action
                containerName: "children"

                Layout.fillWidth: true
            }
        }
    }

    ActionDragDropArea {
        target: _topRule
        dropCallback: function(drop) {
            action.dropAction(drop.text, action.sequenceIndex, "append");
        }
    }

}