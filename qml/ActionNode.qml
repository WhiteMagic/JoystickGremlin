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
import QtQuick.Controls.Universal
import QtQuick.Layouts

import Gremlin.Profile


Item {
    id: _root

    // Data to render
    property ActionModel action
    // Information about the hierarchy of the action sequence
    property ActionModel parentAction
    property string containerName
    // Item rendering information
    property int itemSpacing : 10

    implicitHeight: _content.height

    Connections {
        target: action

        function onActionChanged()
        {
            // Not used currently
        }
    }

    function loadDynamicItem()
    {
        var component = Qt.createComponent(
            Qt.resolvedUrl(_root.action.qmlPath)
        )

        if(component.status == Component.Ready ||
                component.status == Component.Error
        )
        {
            finishCreation();
        }
        else
        {
            component.statusChanged.connect(finishCreation);
        }

        function finishCreation()
        {
            if(component.status === Component.Ready)
            {
                destroyDynamicItem()
                _action.dynamicItem = component.createObject(
                    _action,
                    {
                        action: _root.action
                    }
                );

                // As this object is created within a layout we can
                // use the fillWidth property to ensure this object
                // uses all available space. Height is controlled by
                // the contents of the item and propagate up to the
                // layout itself.
                _action.dynamicItem.Layout.fillWidth = true
            }
            else if(component.status == Component.Error)
            {
                console.log(
                    "Error loading component: ", component.errorString()
                );
            }

            component.destroy()
        }
    }

    function destroyDynamicItem()
    {
        if(_action.dynamicItem != null)
        {
            _action.dynamicItem.destroy()
        }
    }

    // +------------------------------------------------------------------------
    // | Rendering of the node's content
    // +------------------------------------------------------------------------
    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: _root.action.depth > 1 ?
            _foldButton.width + _root.itemSpacing : _root.itemSpacing

        // Drag & drop support
        Drag.active: _dragArea.drag.active
        Drag.dragType: Drag.Automatic
        Drag.supportedActions: Qt.MoveAction
        Drag.proposedAction: Qt.MoveAction
        Drag.mimeData: {
            "text/plain": _root.action.sequenceIndex,
            "type": "action",
            "root": _root.action.rootActionId
        }
        Drag.onDragFinished: function(action)
        {
            // If the drop action ought to be ignore reset the ui by calling
            // the InputConfiguration.qml reload function.
            if(action == Qt.IgnoreAction)
            {
                reload();
            }
        }

        // +--------------------------------------------------------------------
        // | Header
        // +--------------------------------------------------------------------
        RowLayout {
            id: _header

            Layout.fillWidth: true
            Layout.preferredHeight: _foldButton.height
            Layout.bottomMargin: 10
            spacing: 10

            IconButton {
                id: _foldButton

                checkable: true
                checked: backend.isActionExpanded(
                    _root.action.id,
                    _root.action.sequenceIndex
                )
                text: checked ? bsi.icons.folded : bsi.icons.unfolded

                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: -10

                onClicked: {
                    backend.setIsActionExpanded(
                        _root.action.id,
                        _root.action.sequenceIndex,
                        checked
                    )
                }
            }

            Label {
                font.family: "bootstrap-icons"
                font.pixelSize: 24

                text: _root.action.iconString
            }

            TextField {
                id: _headerLabel

                text: _root.action.actionLabel

                background: Rectangle {
                    anchors.fill: parent
                    border.color: Universal.baseLowColor
                }

                onTextEdited: function()
                {
                    _root.action.actionLabel = text
                }
            }

            Rectangle {
                Layout.fillWidth: true
                height: 2
                Layout.alignment: Qt.AlignVCenter

                color: Universal.baseLowColor
            }

            IconButton {
                id: _removeButton

                text: bsi.icons.remove

                onClicked: {
                    parentAction.removeAction(_root.action.sequenceIndex)
                }
            }
        }

        // +--------------------------------------------------------------------
        // | Dynamic QML item loading
        // +--------------------------------------------------------------------
        RowLayout {
            id: _action

            property var dynamicItem: null

            Layout.fillWidth: true
            Layout.leftMargin: _headerLabel.x

            visible: _foldButton.checked

            // Synchronize the container item's height with that of the
            // dynamically created element
            Binding {
                target: _action
                property: "implicitHeight"
                value: _action.dynamicItem === null ? 0 :
                    _action.dynamicItem.implicitHeight
                when: _action.dynamicItem !== null
            }

            // Dynamically load the QML item
            Component.onCompleted: loadDynamicItem()

            // Destroy the dynamic object instance
            Component.onDestruction: destroyDynamicItem()
        }

        Rectangle {
            color: "transparent"
            z: -1
            height: _root.action.lastInContainer ? 15 : 0
            Layout.fillWidth: true
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
        width: _header.width + 20
        height: _header.height

        drag.target: _content
        drag.axis: Drag.YAxis

        // Create an image of the object being dragged for visualization
        onPressed: function()
        {
            _content.grabToImage(function(result)
            {
                _content.Drag.imageSource = result.url
            })
        }
    }

    // Drop area below every non-root action
    Loader {
        active: _root.action.name != "Root"

        sourceComponent: DragDropArea {
            y: (_action.visible ? _action.y + _action.height : _header.y +
                _header.height) - height/2 + itemSpacing/2

            target: _header
            validationCallback: function(drag) {
                return drag.getDataAsString("type") == "action" &&
                    drag.getDataAsString("root") == _root.action.rootActionId
            }
            dropCallback: function(drop) {
                modelData.dropAction(drop.text, modelData.sequenceIndex, "append");
            }
        }
    }
}