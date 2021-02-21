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

    property InputItemBindingModel inputBinding

    implicitHeight: _content.height

    // Content
    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 10
        anchors.rightMargin: 20

        // +--------------------------------------------------------------------
        // | Header
        // +--------------------------------------------------------------------
        ActionConfigurationHeader {
            Layout.fillWidth: true

            inputBinding: _root.inputBinding
        }

        BottomBorder {}


        // +--------------------------------------------------------------------
        // | Render the root action node
        // +--------------------------------------------------------------------
        ActionNode {
            Layout.fillWidth: true

            action: _root.inputBinding.rootAction
        }


        // +--------------------------------------------------------------------
        // | Action selection dropdown
        // +--------------------------------------------------------------------
        Loader {
            Layout.fillWidth: true

            active: _root.inputBinding.actionCount == 0

            sourceComponent: ActionSelector {
                actionNode: _root.inputBinding.rootAction
            }
        }
    }
} // Item