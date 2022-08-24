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
import QtQuick.Window

import QtQuick.Controls.Universal

import Gremlin.Device


Item {
    id: _root

    property string deviceGuid
    property string title

    function compute_height(available_width)
    {
        var rows_required = Math.ceil(
            _grid.count / Math.floor(available_width / _grid.cellWidth)
        )
        return rows_required * _grid.cellHeight + _header.height
    }

    DeviceButtonState {
        id: _button_state

        guid: deviceGuid
    }

    ColumnLayout {
        anchors.left: parent.left
        anchors.right: parent.right

        RowLayout {
            id: _header

            DisplayText {
                text: title + " - Buttons & Hats"
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter

                height: 2
                color: Universal.baseLowColor
            }
        }

        GridView {
            id: _grid

            Layout.fillWidth: true
            Layout.preferredHeight: _root.implicitHeight

            cellWidth: 50
            cellHeight: 50

            model: _button_state
            delegate: Component {
                RoundButton {
                    required property int index
                    required property int identifier
                    required property bool isPressed

                    width: 40
                    height: 40
                    radius: 10

                    text: identifier
                    checked: isPressed
                }
            }
        }
    }

}