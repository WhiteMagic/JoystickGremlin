// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Shapes

import Kobold.Foundation

Item {
    id: _root

    height: Metrics.dp(200)
    width: Metrics.dp(200)

    property point currentValue
    property string text
    property int currentIndex: -1

    // Side length of an equilateral direction marker, and the height that follows from it.
    readonly property int markerSide: Metrics.dp(12)
    readonly property real markerHeight: markerSide * Math.sqrt(3) / 2
    // Distance from centre to each marker's centre, leaving room for the label.
    readonly property real ringRadius:
        Math.min(width, height) / 2 - markerSide / 2 - Metrics.gapS

    onCurrentValueChanged: function()
    {
        // Convert point into an index and store it
        var lut = new Map()
        lut.set(Qt.point(0, 0), -1)
        lut.set(Qt.point(0, 1), 0)
        lut.set(Qt.point(1, 1), 1)
        lut.set(Qt.point(1, 0), 2)
        lut.set(Qt.point(1, -1), 3)
        lut.set(Qt.point(0, -1), 4)
        lut.set(Qt.point(-1, -1), 5)
        lut.set(Qt.point(-1, 0), 6)
        lut.set(Qt.point(-1, 1), 7)

        if(lut.has(currentValue))
        {
            currentIndex = lut.get(currentValue)
        }
    }

    Label {
        anchors.centerIn: parent

        text: _root.text
    }

    Repeater {
        model: 8

        delegate: Shape {
            id: _marker

            required property int index

            readonly property real angle: index * Math.PI / 4

            width: _root.markerSide
            height: _root.markerHeight

            x: _root.width / 2 + _root.ringRadius * Math.sin(angle) - width / 2
            y: _root.height / 2 - _root.ringRadius * Math.cos(angle) - height / 2

            // Drawn pointing north; index 0 is north and each step is 45 degrees clockwise.
            rotation: index * 45

            preferredRendererType: Shape.CurveRenderer

            ShapePath {
                fillColor: _root.currentIndex === _marker.index
                    ? Theme.accent
                    : Theme.fgMuted
                strokeWidth: -1

                startX: _root.markerSide / 2
                startY: 0
                PathLine { x: _root.markerSide; y: _root.markerHeight }
                PathLine { x: 0; y: _root.markerHeight }
                PathLine { x: _root.markerSide / 2; y: 0 }
            }
        }
    }
}
