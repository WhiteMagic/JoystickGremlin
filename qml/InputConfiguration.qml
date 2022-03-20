// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2022 Lionel Ott
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

import Gremlin.Device
import Gremlin.Profile


Item {
    id: _root

    property InputItemBindingListModel inputItemBindingListModel
    property InputIdentifier inputIdentifier

    function reload() {
        _root.inputItemBindingListModel =
            backend.getInputItem(_root.inputIdentifier).inputItemBindings
    }

    onInputIdentifierChanged: {
        _root.inputItemBindingListModel =
            backend.getInputItem(_root.inputIdentifier).inputItemBindings
    }


    ColumnLayout {
        anchors.fill: parent

        ListView {
            id: _listView

            Layout.fillHeight: true
            Layout.fillWidth: true

            spacing: 10

            // Make it behave like a sensible scrolling container
            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AlwaysOn
            }
            flickableDirection: Flickable.VerticalFlick
            boundsBehavior: Flickable.StopAtBounds

            // Content to visualize
            model: _root.inputItemBindingListModel
            delegate: _entryDelegate
        }

        Component {
            id: _entryDelegate

            ActionTree {
                width: _listView.width

                inputBinding: modelData
            }
        }

        // Button to add a new action configuration to the currently
        // active input
        Rectangle {
            id: _newActionButton

            Layout.fillWidth: true
            Layout.preferredHeight: 40

            color: Universal.background

            Button {
                anchors.horizontalCenter: parent.horizontalCenter

                text: "New Action Sequence"

                onClicked: {
                    backend.newInputBinding(_root.inputIdentifier)
                    inputItemBindingListModel.modelReset()
                }
            }

        }
    }
}