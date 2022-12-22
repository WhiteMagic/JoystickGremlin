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


AbstractButton {
    id: _root

    // property alias text: _label.text
    // property bool selected: true
    // signal activated

    // implicitHeight: _container.implicitHeight

    // Rectangle {
    //     implicitHeight: _container.implicitHeight
    //     implicitWidth: parent.width

    //     color: selected ? Universal.chromeMediumColor : Universal.background

    //     RowLayout {
    //         id: _container

    //         Rectangle {
    //             width: 5

    //             Layout.fillHeight: true
    //             Layout.topMargin: 10
    //             Layout.bottomMargin: 10

    //             color: selected ? Universal.accent : Universal.background
    //         }

    //         Label {
    //             id: _label

    //             Layout.fillWidth: true
    //             Layout.topMargin: 10
    //             Layout.bottomMargin: 10
    //         }
    //     }

    //     MouseArea {
    //         anchors.fill: parent

    //         onClicked: function() {
    //             _root.activated()
    //         }
    //     }


        background: Rectangle {
            implicitWidth: 550
            implicitHeight: 66
            opacity: enabled ? 1 : 0.3
            border.color: controlBt.down ? "#17a81a" : "#21be2b"
            border.width: 1
            radius: 2
        }
    }



}