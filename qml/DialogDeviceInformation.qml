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


import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import QtQuick.Controls.Universal

import Gremlin.Device


Window {
    minimumWidth: 900
    minimumHeight: 100
    color: Universal.background
    title: "Device Information"

    DeviceListModel {
        id: deviceData
    }

    ScrollView {
        id: scrollView
        anchors.fill: parent

        GridLayout {
            anchors.fill: parent
            columns: 8

            DisplayText { text: "<b>Name</b>" }
            DisplayText { text: "<b>Axes</b>" }
            DisplayText { text: "<b>Buttons</b>" }
            DisplayText { text: "<b>Hats</b>" }
            DisplayText { text: "<b>VID</b>" }
            DisplayText { text: "<b>PID</b>" }
            DisplayText { text: "<b>Joystick ID</b>" }
            DisplayText { text: "<b>GUID</b>" }

            Repeater {
                model: deviceData
                DisplayText {
                    Layout.row: index + 1
                    Layout.column: 0
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    text: name
                }
            }

            Repeater {
                model: deviceData
                DisplayText {
                    Layout.row: index + 1
                    Layout.column: 1
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    text: axes
                }
            }

            Repeater {
                model: deviceData
                DisplayText {
                    Layout.row: index + 1
                    Layout.column: 2
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    text: buttons
                }
            }

            Repeater {
                model: deviceData
                DisplayText {
                    Layout.row: index + 1
                    Layout.column: 3
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    text: hats
                }
            }

            Repeater {
                model: deviceData
                DisplayText {
                    Layout.row: index + 1
                    Layout.column: 4
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    text: vid
                }
            }

            Repeater {
                model: deviceData
                DisplayText {
                    Layout.row: index + 1
                    Layout.column: 5
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    text: pid
                }
            }

            Repeater {
                model: deviceData
                DisplayText {
                    Layout.row: index + 1
                    Layout.column: 6
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    text: joy_id
                }
            }

            Repeater {
                model: deviceData
                TextField {
                    Layout.row: index + 1
                    Layout.column: 7
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    Layout.preferredWidth: 315

                    text: guid
                    readOnly: true
                    selectByMouse: true
                    font.pointSize: 10
                }
            }
        }

    }
}
