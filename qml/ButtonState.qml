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
        var button_rows = Math.ceil(
            _button_grid.count / Math.floor(available_width / _button_grid.cellWidth)
        )
        var hat_rows = Math.ceil(_hat_grid.count / 2)

        return Math.max(
            button_rows * _button_grid.cellHeight,
            hat_rows * _hat_grid.cellHeight
         ) + _header.height
    }

    DeviceButtonState {
        id: _button_state

        guid: deviceGuid
    }

    DeviceHatState {
        id: _hat_state

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

        RowLayout {
            // Button state display
            GridView {
                id: _button_grid

                Layout.fillWidth: true
                Layout.preferredWidth: 600
                Layout.preferredHeight: _root.implicitHeight
                Layout.alignment: Qt.AlignTop

                boundsMovement: Flickable.StopAtBounds
                boundsBehavior: Flickable.StopAtBounds

                cellWidth: 50
                cellHeight: 50

                model: _button_state
                delegate: Component {
                    RoundButton {
                        required property int index
                        required property int identifier
                        required property bool value

                        width: 40
                        height: 40
                        radius: 10

                        hoverEnabled: false

                        text: identifier
                        checked: value
                    }
                }
            }

            // Hat state display
            GridView {
                id: _hat_grid

                Layout.fillWidth: true
                Layout.minimumWidth: 200
                Layout.preferredWidth: 200
                Layout.preferredHeight: _root.implicitHeight
                Layout.alignment: Qt.AlignTop

                boundsMovement: Flickable.StopAtBounds
                boundsBehavior: Flickable.StopAtBounds

                cellWidth: 100
                cellHeight: 100

                model: _hat_state
                delegate: Component {
                    HatView {
                        required property int identifier
                        required property point value

                        height: _hat_grid.cellHeight - 20
                        width: _hat_grid.cellWidth - 20

                        text: identifier
                        currentValue: value
                    }
                }
            }
        }
    }

}