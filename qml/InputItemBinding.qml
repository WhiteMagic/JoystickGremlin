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
import QtQml.Models

import QtQuick.Controls.Universal

import Gremlin.ActionPlugins
import Gremlin.Profile


Item {
    id: _root

    property InputItemBindingModel inputBinding
    property InputItemBindingConfigurationHeader headerWidget: _header

    implicitHeight: _content.height

    function reload()
    {
        console.log("InputItemBinding::reload")
    }

    Connections {
        target: signal

        function onReloadCurrentInputItem()
        {
            inputBinding.resetSID()
            _action_node.action = inputBinding.rootAction
        }
    }
    

    // Content
    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        // +--------------------------------------------------------------------
        // | Header
        // +--------------------------------------------------------------------
        InputItemBindingConfigurationHeader {
            id: _header

            Layout.fillWidth: true
            Layout.leftMargin: 5
            Layout.rightMargin: 20

            inputBinding: _root.inputBinding
        }

        // +--------------------------------------------------------------------
        // | Render the root action node
        // +--------------------------------------------------------------------
        RootActionNode {
            id: _action_node

            Layout.fillWidth: true
            Layout.rightMargin: 20

            action: _root.inputBinding.rootAction
        }

        HorizontalDivider {
            Layout.fillWidth: true
            Layout.leftMargin: 5
            Layout.rightMargin: 20

            spacing: 15
        }
    }
}