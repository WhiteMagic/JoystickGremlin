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

    function reload() {
        _root.inputItemModel = backend.getInputItem(_root.inputIdentifier)
    }

    onInputIdentifierChanged: {
        _root.inputItemModel = backend.getInputItem(_root.inputIdentifier)
    }

    // Reload UI when the model to display changes
    Connections {
        target: backend

        function onInputConfigurationChanged()
        {
            _root.inputItemModel = backend.getInputItem(_root.inputIdentifier)
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

                height: _actionTree.height + _dropArea.height
                width: _actionTree.width

                required property int index
                required property var modelData
                property ListView view: ListView.view


                ActionTree {
                    id: _actionTree

                    // Have to set the width here as Layout fields don't exist
                    // and we have to fill the view itself which will resize
                    // based on the layout
                    implicitWidth: view.width

                    inputBinding: modelData
                }


                // +------------------------------------------------------------
                // | Drag & Drop support
                // +------------------------------------------------------------
                Connections {
                    target: _actionTree.headerWidget.dragHandleArea
                    function onPressed()
                    {
                        _delegate.grabToImage(function(result)
                        {
                            _delegate.Drag.imageSource = result.url
                        })
                    }
                }

                Drag.active: _actionTree.headerWidget.dragHandleArea.drag.active
                Drag.dragType: Drag.Automatic
                Drag.supportedActions: Qt.MoveAction
                Drag.proposedAction: Qt.MoveAction
                Drag.mimeData: {
                    "text/plain": modelData.actionTreeId,
                    "type": "actiontree"
                }

                Drag.onDragFinished: function(drop)
                {
                    // If the drop action ought to be ignore reset the ui
                    if(drop == Qt.IgnoreAction) {
                        reload();
                    }
                }

                // Drag & Drop drop area
                DragDropArea {
                    id: _dropArea

                    target: _actionTree
                    dropCallback: function(drop) {
                        _root.inputItemModel.dropAction(
                            drop.text,
                            modelData.actionTreeId,
                            "append"
                        )
                    }
                    validationCallback: function(drop) {
                        return drag.getDataAsString("type") == "actiontree"
                    }
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
                    backend.newInputBinding(_root.inputIdentifier)
                }
            }
        }
    }
}