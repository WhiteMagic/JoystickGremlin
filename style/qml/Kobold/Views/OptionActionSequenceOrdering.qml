// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Config
import Kobold.Foundation

Item {
    ActionSequenceOrdering {
        id: _data
    }

    implicitHeight: _content.implicitHeight
    implicitWidth: _content.implicitWidth

    ColumnLayout {
        id: _content
        anchors.fill: parent

        Repeater {
            model: _data

            delegate: ActionDisplay {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignRight

                name: model.name
                active: model.visible
           }
        }

        DropArea {
            id: _bottomDropArea

            Layout.fillWidth: true
            Layout.preferredHeight: Metrics.controlHeight

            onDropped: (drop) => {
                _data.move(drop.text, _data.rowCount())
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                y: 0
                height: 2

                color: Theme.accent
                opacity: parent.containsDrag ? 1.0 : 0.0
            }
        }
    }

    component ActionDisplay : Item {
        property alias name: _label.text
        property alias active: _switch.checked

        implicitHeight: _item.implicitHeight

        RowLayout {
            id: _item

            anchors.left: parent.left
            anchors.right: parent.right
            height: parent.height

            property int index: model.index
            property bool isDragging: false

            Drag.active: isDragging
            Drag.dragType: Drag.Automatic
            Drag.supportedActions: Qt.MoveAction
            Drag.proposedAction: Qt.MoveAction
            Drag.source: _item
            Drag.hotSpot.x: width / 2
            Drag.hotSpot.y: height / 2
            Drag.mimeData: ({
                "text/plain": model.index.toString()
            })

            ToolButton {
                icon.name: "grip"

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
                        _item.y = 0
                    }
                }
            }

            Label {
                id: _label

                Layout.fillWidth: true
            }

            CheckBox {
                id: _switch

                text: checked ? "On" : "Off"

                onToggled: () => { model.visible = checked }
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
                height: 2
                y: parent.height / 2

                color: Theme.accent
                opacity: parent.containsDrag ? 1.0 : 0.0
            }
        }
    }
}
