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
import QtQuick.Layouts 1.14
import QtQuick.Controls.Universal 2.14


Item {
    height: _border.height

    Rectangle {
        id: _border

        width: parent.width
        height: _line.height + _line.anchors.topMargin + _line.anchors.bottomMargin

        Rectangle {
            id: _line

            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.topMargin: 5
            anchors.bottomMargin: 10

            height: 2

            color: Universal.accent
        }
    }
}