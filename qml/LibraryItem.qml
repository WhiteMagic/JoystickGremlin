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
    property int itemSpacing : 10

    height: _baseItem.height
    width: parent.width

    Item {
        id: _baseItem

        property int sourceY
        property bool dragSuccess : false

        // Dimensions
        height: _header.height + _headerSpacer.height + _action.height + _actionSelector.height

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 10 + 20 * (model.depth - 1)

        // Drag & drop support
        Drag.active: _dragArea.drag.active
        Drag.dragType: Drag.Automatic
        Drag.supportedActions: Qt.MoveAction
        Drag.proposedAction: Qt.MoveAction
        Drag.mimeData: {
            "text/plain": model.id
        }
        Drag.onDragFinished: {
            _baseItem.dragSuccess = dropAction == Qt.MoveAction;
        }
        Drag.onDragStarted: {
            _baseItem.sourceY = _baseItem.y
        }

        // Header
        Row {
            id: _header

            anchors.top: _baseItem.top
            spacing: 10

            FoldButton {
                id: _actionButton

                checked: backend.isActionExpanded(model.id)
                icon.source: checked ? "../gfx/button_delete.png" : "../gfx/button_add.png"

                onClicked: {
                    backend.setIsActionExpanded(model.id, checked)
                }
            }

            Label {
                id: _actionName

                anchors.verticalCenter: _actionButton.verticalCenter

                text: model.name
            }

            Rectangle {
                id: _headerSeparator

                height: 2
                width: _baseItem.width - _actionButton.width - _actionName.width - 2 * _header.spacing - 10
                anchors.verticalCenter: _actionButton.verticalCenter

                color: _actionButton.background.color
            }
        }

        BottomSpacer {
            id: _headerSpacer

            item: _header
            spacing: _action.visible ? itemSpacing : 0
        }

        // Drag interface area
        MouseArea {
            id: _dragArea

            // Start at label field x coordinate, otherwise button stops working
            x: _actionName.x
            y: _header.y
            width: _actionName.width + _headerSeparator.width
            height: _header.height

            drag.target: _baseItem
            drag.axis: Drag.YAxis

            onReleased: {
                if(!_baseItem.dragSuccess)
                {
                    _baseItem.y = _baseItem.sourceY;
                }
            }

            // Create an image of the object to visualize the dragging
            onPressed: _baseItem.grabToImage(function(result) {
                _baseItem.Drag.imageSource = result.url
            })
        }

        // Drop area
        DropArea {
            id: _dropArea

            height: _header.height + itemSpacing
            anchors.left: _header.left
            anchors.right: _header.right
            y: _action.y + _action.height - height/2 + itemSpacing/2

            // Visualization of the drop indicator
            Rectangle {
                id: _dropMarker

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter

                height: 5

                opacity: _dropArea.containsDrag ? 1.0 : 0.0
                color: Universal.accent
            }

            onDropped: {
                if(drop.text != model.id)
                {
                    drop.accept();
                    _listView.model.moveAfter(drop.text, model.id);
                }
            }
        }

        // Dynamic QML item loading
        Item {
            id: _action

            anchors.left: _baseItem.left
            anchors.right: _baseItem.right
            anchors.top: _headerSpacer.bottom
            
            height: visible ? implicitHeight : 0
            
            visible: _actionButton.checked

            // Dynamically load the QML item
            Component.onCompleted: {
                var component = Qt.createComponent(Qt.resolvedUrl(qmlPath));
                if (component) {
                    if (component.status == Component.Ready) {
                        var obj = component.createObject(
                            _action,
                            {
                                model: profileData,
                                actionConfiguration: action
                            }
                        );

                        _action.implicitHeight = obj.height;
                        obj.anchors.left = _action.left;
                        obj.anchors.right = _action.right;

                    } else if (component.status == Component.Error) {
                        console.log("Error loading component:", component.errorString());
                    }
                }
            }
        }

        // On each valid level/item need to have a dropdown with actions
        Loader {
            id: _actionSelector
            anchors.top: _action.bottom

            active: model.isLastSibling

            sourceComponent: Column {
                Rectangle {
                    height: itemSpacing
                    width: 1
                }
                ActionSelector {
                    configuration: action
                }
            }

        }

    } // Item

} // Component (delegate)