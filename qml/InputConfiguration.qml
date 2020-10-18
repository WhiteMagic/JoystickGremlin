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
import QtQuick.Window 2.14

import QtQuick.Controls.Universal 2.14

import gremlin.ui.profile 1.0
import gremlin.ui.device 1.0


Item {
    id: _root

    property ActionConfigurationListModel actionConfigurationListModel
    property InputIdentifier inputIdentifier

    function reload() {
        _root.actionConfigurationListModel =
            backend.getInputItem(_root.inputIdentifier).actionConfigurations
    }

    onInputIdentifierChanged: {
        _root.actionConfigurationListModel =
            backend.getInputItem(_root.inputIdentifier).actionConfigurations
    }

    Component.onCompleted: {
        console.log(width + " " + height + " | " + x + " " + y)
    }

    Column {
        //width: parent.width
        anchors.left: parent.left
            anchors.right: parent.right

        ListView {
            id: _listView

            anchors.left: parent.left
            anchors.right: parent.right

            spacing: 10

            // Make it behave like a sensible scrolling container
            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AlwaysOn
            }
            flickableDirection: Flickable.VerticalFlick
            boundsBehavior: Flickable.StopAtBounds

            // Content to visualize
            model: actionConfigurationListModel
            delegate: _entryDelegate
        }

        Component {
            id: _entryDelegate

            ActionTree {
                width: _listView.width

                actionTree: modelData
            }

        }

        // Button to add a new action configuration to the currently
        // active input
        Rectangle {
            id: _newActionButton
            
            width: parent.width
            height: 40

            color: Universal.background

            Button {
                anchors.horizontalCenter: parent.horizontalCenter

                text: "Create new action sequence"
                
                onClicked: {
                    backend.newActionConfiguration(_root.inputIdentifier)
                    actionConfigurationListModel.modelReset()
                }
            }

        }
    }
}