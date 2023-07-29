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

import Gremlin.Device
import Gremlin.Profile


Item {
    id: _root

    property InputIdentifier inputIdentifier
    property InputItemModel inputItemModel

    function reload()
    {
        _root.inputItemModel = backend.getInputItem(_root.inputIdentifier)
    }

    onInputIdentifierChanged: {
        reload()
    }

    // Reload UI when the model to display changes
    Connections {
        target: backend

        function onInputConfigurationChanged()
        {
            reload()
        }
    }

    Connections {
        target: signal

        function onReloadCurrentInputItem()
        {
            reload()
        }
    }

    // Widget content
    ColumnLayout {
        id: _content

        anchors.fill: parent

        // Show all actions associated with this input
        ListView {
            id: _listView

            Layout.fillHeight: true
            Layout.fillWidth: true

            // Make it behave like a sensible scrolling container
            ScrollBar.vertical: ScrollBar {
                policy: ScrollBar.AlwaysOn
            }
            flickableDirection: Flickable.VerticalFlick
            boundsBehavior: Flickable.StopAtBounds

            // Content to visualize
            model: _root.inputItemModel.inputItemBindings
            delegate: _entryDelegate
        }

        // ListView delegate definition rendering individual bindings
        // via ActionTree instances
        Component {
            id: _entryDelegate

            Item {
                id: _delegate

                height: _binding.height
                width: _binding.width

                required property int index
                required property var modelData
                property ListView view: ListView.view

                InputItemBinding {
                    id: _binding

                    // Have to set the width here as Layout fields don't exist
                    // and we have to fill the view itself which will resize
                    // based on the layout
                    implicitWidth: view.width

                    inputBinding: modelData
                }
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
                    _root.inputItemModel.createNewActionSequence()
                }
            }
        }
    }
}