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

    height: 100
    width: 100

    Repeater {
        model: 8

        transform: Translate {
            x: 50
            y: 50
        }

        delegate: Triangle {
            required property int index

            width: 15
            height: 15
            color: "blue"

            transform: [
                Translate { y: -50},
                Rotation { angle: index*45 }
            ]
        }
    }
}