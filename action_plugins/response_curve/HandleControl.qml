// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Shapes

import Gremlin.Style
import "render_helpers.js" as RH

Rectangle {
    id: _control

    readonly property int offset: 5
    property Repeater repeater
    property Item focusTarget

    property alias leftHandle: _handleLeft
    property alias rightHandle: _handleRight

    width: offset * 2
    height: offset * 2
    radius: offset

    color: action.selectedPoint === index ? Style.accent : Style.medColor

    function updateHandle(handle, evt, side) {
        // Compute new data values.
        let new_x = RH.clamp(map2x(_control.x + handle.x, evt.x), -1.0, 1.0)
        let new_y = RH.clamp(map2y(_control.y + handle.y, evt.y), -1.0, 1.0)

        // Compute new visual values.
        let new_u = ((new_x - modelData.center.x) / 2.0) * _vis.size
        let new_v = -((new_y - modelData.center.y) / 2.0) * _vis.size

        // Handle symmetry mode, no need to update model as the code does this
        // behind the scenes with the model update below.
        if (_root.action.isSymmetric) {
            let mirror = repeater.itemAt(repeater.count - index - 1).item
            let dx = new_u - handle.x
            let dy = new_v - handle.y

            if(side === "left") {
                mirror.rightHandle.x -= dx
                mirror.rightHandle.y -= dy
            }
            else if(side === "right") {
                mirror.leftHandle.x -= dx
                mirror.leftHandle.y -= dy
            }
        }

        // With mirrored handles the opposing handle of this same point is the
        // point reflection of the one being dragged.
        if (modelData.symmetricHandles) {
            let opposite = side === "left" ? _handleRight : _handleLeft
            opposite.x = -new_u
            opposite.y = -new_v
        }

        // Move the actual marker then update data model.
        handle.x = new_u
        handle.y = new_v
        action.setControlHandle(new_x, new_y, index, side, true)
    }

    x: map2u(modelData.center.x)
    y: map2v(modelData.center.y)

    // Rendering of the control point handles and their connection line.
    Shape {
        preferredRendererType: Shape.CurveRenderer
        z: -1

        // Left control handle line.
        ShapePath {
            strokeColor: modelData.hasLeft ? "#808080" : "transparent"

            startX: offset
            startY: offset

            PathLine {
                x: _handleLeft.x + offset
                y: _handleLeft.y + offset
            }
        }

        // Right control handle line.
        ShapePath {
            strokeColor: modelData.hasRight ? "#808080" : "transparent"

            startX: offset
            startY: offset

            PathLine {
                x: _handleRight.x + offset
                y: _handleRight.y + offset
            }
        }

        // Left control handle.
        Rectangle {
            id: _handleLeft

            visible: modelData.hasLeft

            x: ((modelData.handleLeft.x - modelData.center.x) / 2.0) * _vis.size
            y: -((modelData.handleLeft.y - modelData.center.y) / 2.0) * _vis.size

            width: offset * 2
            height: offset * 2

            color: Style.background
            border.color: action.selectedPoint === index ? Style.accent : Style.medColor
            border.width: 2

            MouseArea {
                anchors.fill: parent
                preventStealing: true

                onPositionChanged: (evt) => {
                    updateHandle(parent, evt, "left")
                }
                onPressed: () => {
                    action.selectedPoint = index
                    focusTarget.forceActiveFocus()
                }
                onReleased: () => { action.redrawElements() }
            }
        }

        // Right control handle.
        Rectangle {
            id: _handleRight

            visible: modelData.hasRight

            x: ((modelData.handleRight.x - modelData.center.x) / 2.0) * _vis.size
            y: -((modelData.handleRight.y - modelData.center.y) / 2.0) * _vis.size

            width: offset * 2
            height: offset * 2

            color: Style.background
            border.color: action.selectedPoint === index ? Style.accent : Style.medColor
            border.width: 2

            MouseArea {
                anchors.fill: parent
                preventStealing: true

                onPositionChanged: (evt) => {
                    updateHandle(parent, evt, "right")
                }
                onPressed: () => {
                    action.selectedPoint = index
                    focusTarget.forceActiveFocus()
                }
                onReleased: () => { action.redrawElements() }
            }
        }
    }

    // Rendering of the control point itself.
    MouseArea {
        anchors.fill: parent
        preventStealing: true

        onPositionChanged: (evt) => {
            let coord = updateControlPoint(parent, evt, index)
            if(coord !== null) {
                action.setControlHandle(coord[0], coord[1], index, "center", true)
            }
        }
        onPressed: () => {
            action.selectedPoint = index
            focusTarget.forceActiveFocus()
        }
        onReleased: () => { action.redrawElements() }
    }
}
