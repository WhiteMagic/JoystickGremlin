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
import QtQuick.Layouts 1.14

import gremlin.ui.profile 1.0


Item {
    id: _root

    property ActionNodeModel action
    property ActionTreeModel actionTree
    property int itemSpacing : 10

    implicitHeight: _content.childrenRect.height

    onImplicitHeightChanged: {
        console.log("ActionNode " + implicitHeight)
        parent.implicitHeight = implicitHeight
    }

    ColumnLayout {
        id: _content

        property int sourceY
        property bool dragSuccess : false

        anchors.left: parent.left
        anchors.right: parent.right

        // Drag & drop support
//        Drag.active: _dragArea.drag.active
//        Drag.dragType: Drag.Automatic
//        Drag.supportedActions: Qt.MoveAction
//        Drag.proposedAction: Qt.MoveAction
//        Drag.mimeData: {
//            "text/plain": _root.action.id
//        }
//        Drag.onDragFinished: {
//            _content.dragSuccess = dropAction == Qt.MoveAction;
//        }
//        Drag.onDragStarted: {
//            _content.sourceY = _content.y
//        }

        // Header
        RowLayout {
            id: _header

            Layout.fillWidth: true
            Layout.preferredHeight: _foldButton.height
            spacing: 10

            FoldButton {
                id: _foldButton

                checked: backend.isActionExpanded(_root.action.id)
                icon.source: checked ? "../gfx/button_delete.png" : "../gfx/button_add.png"

                onClicked: {
                    backend.setIsActionExpanded(_root.action.id, checked)


//                    _action.visible = checked
//                    var height = checked ? _action.itemHeight : 0
//                    _action.Layout.preferredHeight = height
//                    _action.height = height
                    _action.height = _action.Layout.preferredHeight
                }
            }

            Label {
                text: _root.action.name
            }

            Rectangle {
                Layout.fillWidth: true
                height: 2
                Layout.alignment: Qt.AlignVCenter

                color: _foldButton.background.color
            }

            Button {
                icon.source: "../gfx/delete.svg"

// FIXME: Reimplement this
//                onClicked: {
//                    _listView.model.remove(model.id);
//                }
            }
        }

//        VerticalSpacer {
//            spacing: _action.visible ? itemSpacing : 0
//        }

        // Dynamic QML item loading
        Item {
            id: _action

            property int itemHeight : 0

            Layout.fillWidth: true
            Layout.preferredHeight: _foldButton.checked ? itemHeight : 0
            visible: _foldButton.checked

            // Dynamically load the QML item
            Component.onCompleted: {
                var component = Qt.createComponent(
                    Qt.resolvedUrl(_root.action.qmlPath)
                )

                if (component) {
                    if (component.status == Component.Ready) {
                        var obj = component.createObject(
                            _action,
                            {
                                model: _root.action.actionModel,
                                actionTree: actionTree
                            }
                        );

                        _action.itemHeight = obj.implicitHeight
                        obj.anchors.left = _action.left
                        obj.anchors.right = _action.right

//                        var obj = Qt.createQmlObject(
//                            '
//                                import QtQuick 2.14
//                                import QtQuick.Layouts 1.14
//
//                                Item {
//                                    height: _layout.height
//
//                                    ColumnLayout {
//                                        id: _layout
//
//                                        anchors.left: parent.left
//                                        anchors.right: parent.right
//
//                                        Rectangle {
//                                            color: "red"
//                                            height: 20
//
//                                            Layout.fillWidth: true
//                                        }
//                                    }
//                                }
//                            ',
//                            _action,
//                            "dynamicSnippet1"
//                        );
//                        _action.implicitHeight = obj.height
//                        obj.anchors.left = _action.left
//                        obj.anchors.right = _action.right
                    } else if (component.status == Component.Error) {
                        console.log("Error loading component:", component.errorString());
                    }
                }
            }
        }

        // On each valid level/item need to have a dropdown with actions
//        Loader {
//            id: _actionSelector
//
//            active: _root.action.isLastSibling
//
//            sourceComponent: Column {
//                Rectangle {
//                    height: itemSpacing
//                    width: 1
//                }
//                ActionSelector {
//                    actionTree: _root.actionTree
//                }
//            }
//        }

    //} // Item
    }

/*
    // +------------------------------------------------------------------------
    // | Drag & Drop support
    // +------------------------------------------------------------------------
    // Drag interface area
    MouseArea {
        id: _dragArea

        // Start at label field x coordinate, otherwise button stops working
        x: _actionName.x
        y: _header.y
        width: _actionName.width + _headerSeparator.width
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
            if(drop.text != _root.action.id)
            {
                drop.accept();
                // FIXME: reimplement this
                //_listView.model.moveAfter(drop.text, model.id);
            }
        }
    }

    // Drop area atop the header
    Loader {
        //anchors.left: _header.left
        //anchors.right: _header.right

        active: _root.action.isFirstSibling
        sourceComponent: DropArea {
            id: _topDropArea

            height: _header.height
            anchors.left: parent.left
            anchors.right: parent.right
            y: _header.y - itemSpacing

            // Visualization of the drop indicator
            Rectangle {
                id: _topDropMarker

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top

                height: 5

                opacity: _topDropArea.containsDrag ? 1.0 : 0.0
                color: Universal.accent
            }

            onDropped: {
                if(drop.text != _root.action.id)
                {
                    drop.accept();
                    // FIXME: reimplement this
                    //_listView.model.moveBefore(drop.text, model.id);
                }
            }
        }
    }
*/

} // Component (delegate)