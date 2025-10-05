// -*- coding: utf-8; -*-
//
// Copyright (C) 2025 Lionel Ott
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

import Gremlin.Config


Item {
    ActionSequenceOrdering {
        id: _data
    }

    implicitHeight: _content.implicitHeight + _bottomDropArea.height


    ColumnLayout {
        anchors.fill: parent

        ListView {
            id: _content

            width: parent.width
            implicitHeight: contentHeight

            model: _data

            delegate: ActionDisplay {
                name: model.name
                active: model.visible

                width: ListView.view.width
            }
        }

        DropArea {
            id: _bottomDropArea

            Layout.fillWidth: true
            height: 20

            onDropped: (drop) => {
                _data.move(drop.text, _data.rowCount())
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                y: 0
                height: 1

                color: "steelblue"
                opacity: parent.containsDrag ? 1.0 : 0.0
            }
        }
    }

    component ActionDisplay : Item {
        property alias name: _switch.text
        property alias active: _switch.checked

        implicitHeight: _item.implicitHeight

        RowLayout {
            id: _item

            anchors.fill: parent
            property int index: model.index
            property bool isDragging: false

            Drag.active: isDragging
            Drag.dragType: Drag.Automatic
            Drag.supportedActions: Qt.MoveAction
            Drag.proposedAction: Qt.MoveAction
            Drag.source: _item
            Drag.hotSpot.x: width / 2
            Drag.hotSpot.y: height / 2
            Drag.mimeData: {
                "text/plain": model.index.toString()
            }

            IconButton {
                text: bsi.icons.drag_handle

                // Drag handle interaction for drag&drop suppport.
                MouseArea {
                    id: _dragArea

                    anchors.fill: parent
                    drag.target: _item
                    drag.axis: Drag.YAxis

                    // Create an image of the object being dragged for visualization
                    onPressed: () => {
                        _item.isDragging = true
                        _item.grabToImage((result) => {
                            _item.Drag.imageSource = result.url
                        })
                    }

                    onReleased: () => {
                        _item.isDragging = false
                    }
                }
            }
            CompactSwitch {
                id: _switch

                Layout.fillWidth: true

                onToggled: () => {
                    model.visible = checked
                }
            }
        }

        DropArea {
            id: _dropArea
            anchors.left: parent.left
            anchors.right: parent.right
            height: _item.height
            y: _item.y - height/2

            onDropped: (drop) => {
                _data.move(drop.text, index)
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                height: 1
                y: parent.height / 2

                color: "steelblue"
                opacity: parent.containsDrag ? 1.0 : 0.0
            }
        }
    }
}
