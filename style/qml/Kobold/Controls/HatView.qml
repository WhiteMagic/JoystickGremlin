// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Kobold.Foundation

Item {
    id: _root

    height: Metrics.hatViewSize
    width: Metrics.hatViewSize

    property point currentValue
    property string text
    property int currentIndex: -1

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

        delegate: Rectangle {
            required property int index

            width: Metrics.hatViewDotSize
            height: Metrics.hatViewDotSize
            radius: 2
            color: _root.currentIndex === index ? Theme.accent : Theme.line

            transform: [
                Translate {
                    x: _root.width / 2 - width / 2
                    y: 0
                },
                Rotation {
                    angle: index*45
                    origin {
                        x: _root.width / 2
                        y: _root.height / 2
                    }
                }
            ]
        }
    }
}
