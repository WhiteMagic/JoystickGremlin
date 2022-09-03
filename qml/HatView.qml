// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2022 Lionel Ott
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
import QtQuick.Shapes
import QtQuick.Window

import QtQuick.Controls.Universal

import Gremlin.Device


Item {
    id: _root

    height: 200
    width: 200

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

        delegate: Triangle {
            required property int index

            width: 15
            height: 15
            color: _root.currentIndex == index ? Universal.accent : Universal.baseLowColor

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