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
import QtQml.Models 2.14

import QtQuick.Controls.Universal 2.14

import gremlin.ui.profile 1.0


Item {
    id: _root

    property ActionTreeModel actionTree

    implicitHeight: _content.height

    // Content
    ColumnLayout {
        id: _content

        anchors.left: _root.left
        anchors.right: _root.right
        anchors.leftMargin: 10
        anchors.rightMargin: 20

        // +--------------------------------------------------------------------
        // | Header
        // +--------------------------------------------------------------------
        ActionConfigurationHeader {
            id: _header

            Layout.fillWidth: true

            actionTree: _root.actionTree
        }

        BottomBorder {}


        // +--------------------------------------------------------------------
        // | Render the root action node
        // +--------------------------------------------------------------------
        ActionNode {
            id: _action

            Layout.fillWidth: true

            action: _root.actionTree.rootAction
            actionTree: _root.actionTree
        }


        // +--------------------------------------------------------------------
        // | Action selection dropdown
        // +--------------------------------------------------------------------
        Loader {
            id: _actionSelector

            Layout.fillWidth: true

            active: actionTree.actionCount == 0

            sourceComponent: ActionSelector {
                actionTree: actionTree
            }
        }
    }
} // Item