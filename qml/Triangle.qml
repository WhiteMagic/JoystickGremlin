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
import QtQuick.Shapes


Shape {
    id: _shape

    property alias color: _path.fillColor

    ShapePath {
        id: _path

        startX: 0
        startY: _shape.height

        PathLine { x: _shape.width/2; y: 0 }
        PathLine { x: _shape.width; y: _shape.height }
        PathLine { x: 0; y: _shape.height }
    }
}