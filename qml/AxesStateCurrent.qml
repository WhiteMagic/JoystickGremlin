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
        return _list.height + _header.height
    }

    function format_percentage(value)
    {
        return Math.round(value * 100)
    }

    DeviceAxisState {
        id: _axis_state

        guid: deviceGuid
    }

    ColumnLayout {
        anchors.left: parent.left
        anchors.right: parent.right

        RowLayout {
            id: _header

            DisplayText {
                text: title + " - Axes"
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter

                height: 2
                color: Universal.baseLowColor
            }
        }

        ListView {
            id: _list

            Layout.fillWidth: true
            Layout.preferredHeight: 150

            orientation: Qt.Horizontal
            spacing: 10

            model: _axis_state
            delegate: Component {
                ColumnLayout {
                    required property int index
                    required property int identifier
                    required property double axisValue

                    height: ListView.view.height
                    width: 60

                    Label {
                        Layout.alignment: Qt.AlignHCenter

                        text: "Axis " +  identifier
                    }
                    VerticalProgressBar {
                        Layout.fillHeight: true
                        Layout.alignment: Qt.AlignHCenter

                        from: -1
                        to: 1
                        value: axisValue
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter

                        text: format_percentage(axisValue) + " %"
                    }

                }
            }
        }
    }

}