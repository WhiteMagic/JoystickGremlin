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

import QtQuick.Controls.Universal 2.14

import gremlin.ui.profile 1.0


Item {
    property ActionConfigurationModel action

    height: idBaseItem.height
    width: parent.width

    Item {
        id: idBaseItem

        property int sourceY
        property bool dragSuccess : false

        // Dimensions
        height: {
            if(idActionButton.checked) {
                idActionButton.height + idAction.height
            } else {
                idActionButton.height
            }
        }
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 10 + 20 * (model.depth - 1)

        // Drag & drop support
        Drag.active: idDragArea.drag.active
        Drag.dragType: Drag.Automatic
        Drag.supportedActions: Qt.MoveAction
        Drag.proposedAction: Qt.MoveAction
        Drag.mimeData: {
            "text/plain": model.id
        }
        Drag.onDragFinished: {
            idBaseItem.dragSuccess = dropAction == Qt.MoveAction;
        }
        Drag.onDragStarted: {
            idBaseItem.sourceY = idBaseItem.y
        }

        // Header
        Row {
            id: idActionHeader

            anchors.top: idBaseItem.top
            spacing: 10

            FoldButton {
                id: idActionButton

                checked: backend.isActionExpanded(model.id)
                icon.source: checked ? "../gfx/button_delete.png" : "../gfx/button_add.png"

                onClicked: {
                    backend.setIsActionExpanded(model.id, checked)
                }
            }

            Label {
                id: idActionName

                anchors.verticalCenter: idActionButton.verticalCenter

                text: model.name
            }

            Rectangle {
                id: idSeparator

                height: 2
                width: idBaseItem.width - idActionButton.width - idActionName.width - 2 * idActionHeader.spacing - 10
                anchors.verticalCenter: idActionButton.verticalCenter

                color: idActionButton.background.color
            }
        }

        // Drag interface area
        MouseArea {
            id: idDragArea

            x: idActionName.x
            y: idActionHeader.y
            width: idActionName.width + idSeparator.width
            height: idActionHeader.height

            drag.target: idBaseItem
            drag.axis: Drag.YAxis

            onReleased: {
                if(!idBaseItem.dragSuccess)
                {
                    idBaseItem.y = idBaseItem.sourceY;
                }
            }

            // Create an image of the object to visualize the dragging
            onPressed: idBaseItem.grabToImage(function(result) {
                idBaseItem.Drag.imageSource = result.url
            })
        }

        // Drop area
        DropArea {
            id: idDropArea

            height: idBaseItem.height
            anchors.left: idBaseItem.left
            anchors.right: idBaseItem.right
            anchors.top: idBaseItem.verticalCenter

            // Visualization of the drop indicator
            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.verticalCenter

                height: 5

                opacity: idDropArea.containsDrag ? 1.0 : 0.0
                color: Universal.accent
            }

            onDropped: {
                if(drop.text != model.id)
                {
                    drop.accept();
                    idListView.model.moveAfter(drop.text, model.id);
                }
            }
        }

        // Dynamic QML item loading
        Item {
            id: idAction

            anchors.left: idBaseItem.left
            anchors.right: idBaseItem.right
            anchors.top: idActionHeader.bottom
            anchors.topMargin: 10
            visible: idActionButton.checked

            // Dynamically load the QML item
            Component.onCompleted: {
                var component = Qt.createComponent(Qt.resolvedUrl(qmlPath));
                if (component) {
                    if (component.status == Component.Ready) {
                        var obj = component.createObject(
                            idAction,
                            {
                                model: profileData,
                                actionConfiguration: action
                            }
                        );

                        idAction.height = obj.height;
                        obj.anchors.left = idAction.left;
                        obj.anchors.right = idAction.right;

                    } else if (component.status == Component.Error) {
                        console.log("Error loading component:", component.errorString());
                    }
                }
            }
        }

    } // Item

} // Component (delegate)