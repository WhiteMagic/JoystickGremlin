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
import QtQuick.Layouts
import QtQuick.Window

import QtQuick.Controls.Universal

import Gremlin.ActionPlugins
import Gremlin.Profile
import "../../qml"


Item {
    id: _root

    property RootModel action

    implicitHeight: _content.height

    // Show all child nodes
    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

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