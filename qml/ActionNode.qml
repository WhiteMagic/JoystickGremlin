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


import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts

import gremlin.ui.profile


Item {
    id: _root

    property ActionNodeModel action
    property int itemSpacing : 10

    implicitHeight: _content.height

    // +------------------------------------------------------------------------
    // | Rendering of the node's content
    // +------------------------------------------------------------------------
    ColumnLayout {
        id: _content

        property int sourceY
        property bool dragSuccess : false

        anchors.left: parent.left
        anchors.right: parent.right

        // Drag & drop support
        Drag.active: _dragArea.drag.active
        Drag.dragType: Drag.Automatic
        Drag.supportedActions: Qt.MoveAction
        Drag.proposedAction: Qt.MoveAction
        Drag.mimeData: {
            "text/plain": _root.action.id
        }
        Drag.onDragFinished: {
            _content.dragSuccess = dropAction == Qt.MoveAction;
        }
        Drag.onDragStarted: {
            _content.sourceY = _content.y
        }

        // Header
        RowLayout {
            id: _header

            Layout.fillWidth: true
            Layout.preferredHeight: _foldButton.height
            spacing: 10

            IconButton {
                id: _foldButton

                checked: backend.isActionExpanded(_root.action.id)
                text: checked ? "\uf146" : "\uf0fe"

                onClicked: {
                    backend.setIsActionExpanded(_root.action.id, checked)
                }
            }

            Label {
                text: `<b>${_root.action.name}</b>`
            }

            Rectangle {
                Layout.fillWidth: true
                height: 2
                Layout.alignment: Qt.AlignVCenter

                color: Universal.baseLowColor
            }

            IconButton {
                text: "\uf2ed"

                onClicked: {
                   modelData.remove()
                }
            }
        }

        // Dynamic QML item loading
        Item {
            id: _action

            property var dynamicItem: null

            Layout.fillWidth: true
            Layout.preferredHeight: _foldButton.checked ? implicitHeight : 0
            visible: _foldButton.checked

            Connections {
                target: _action.dynamicItem
                function onImplicitHeightChanged() {
                    _action.implicitHeight = _action.dynamicItem.implicitHeight
                }
            }

            // Dynamically load the QML item
            Component.onCompleted: {
                var component = Qt.createComponent(
                    Qt.resolvedUrl(_root.action.qmlPath)
                )

                if (component) {
                    if (component.status == Component.Ready) {
                        _action.dynamicItem = component.createObject(
                            _action,
                            {
                                node: _root.action,
                                action: _root.action.actionModel
                            }
                        );

                        _action.implicitHeight = _action.dynamicItem.implicitHeight
                        _action.dynamicItem.anchors.left = _action.left
                        _action.dynamicItem.anchors.right = _action.right
                        _action.dynamicItem.anchors.leftMargin = _foldButton.width
                    } else if (component.status == Component.Error) {
                        console.log("Error loading component:", component.errorString());
                    }
                }
            }
        }
    }


    // +------------------------------------------------------------------------
    // | Drag & Drop support
    // +------------------------------------------------------------------------
    
    // Drag interface area
    MouseArea {
        id: _dragArea

        // Start at label field x coordinate, otherwise button stops working
        x: _header.x
        y: _header.y
        z: -1
        width: _header.width
        height: _header.height

        drag.target: _content
        drag.axis: Drag.YAxis

        onReleased: {
            if(!_content.dragSuccess)
            {
                _content.y = _content.sourceY;
            }
        }

        // Create an image of the object to visualize the dragging
        onPressed: _content.grabToImage(function(result) {
            _content.Drag.imageSource = result.url
        })
    }

    // Drop area below every non-root action
    Loader {
        active: !_root.action.isRootNode
        sourceComponent: DropArea {
            x: _action.x
            y: (_action.visible ? _action.y + _action.height : _header.y + _header.height) - height/2 + itemSpacing/2
            width: _action.width
            height: 30

            // Visualization of the drop indicator
            Rectangle {
                id: _dropMarker

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter

                height: 5

                opacity: parent.containsDrag ? 1.0 : 0.0
                color: Universal.accent
            }

            onDropped: {
                if(drop.text != _root.action.id)
                {
                    drop.accept();
                    modelData.dropAction(drop.text, modelData.id, "append");
                }
            }
        }
    }
}