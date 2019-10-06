// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2019 Lionel Ott
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


import QtQuick 2.13
import QtQuick.Controls 2.13
import QtQuick.Layouts 1.13
import QtQuick.Window 2.13

import QtQuick.Controls.Universal 2.12

import gremlin.ui.device_data 1.0


Window {
    minimumWidth: 800
    minimumHeight: 200
    color: Universal.background
    title: "Device Information"

    ScrollView {
        id: scrollView
        anchors.fill: parent

        DeviceData {
            id: deviceData
        }

        ListView {
            id: listView
            anchors.fill: parent

            model: deviceData
            delegate: deviceDelegate
            header: headerComponent

            boundsBehavior: Flickable.StopAtBounds
        }

        Component {
            id: deviceDelegate

            Item {
                width: parent.width
                height: idGuid.height + 10

                Label {
                    id: idName
                    text: name
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                }

                Label {
                    text: axes
                    width: 75
                    anchors.right: idButtons.left
                }
                Label {
                    id: idButtons
                    text: buttons
                    width: 75
                    anchors.right: idHats.left
                }
                Label {
                    id: idHats
                    text: hats
                    width: 75
                    anchors.right: idVid.left
                }
                Label {
                    id: idVid
                    text: vid
                    width: 75
                    anchors.right: idPid.left
                }
                Label {
                    id: idPid
                    text: pid
                    width: 75
                    anchors.right: idGuid.left
                }
                TextField {
                    id: idGuid
                    text: guid
                    width: 315
                    anchors.right: parent.right
                    anchors.rightMargin: 10
                    readOnly: true
                    selectByMouse: true
                }

            }
        }

        Component {
            id: headerComponent

            Rectangle {
                width: parent.width
                //height: idName.height + 10
                height: 50
                color: Universal.chromeMediumColor
                anchors.left: parent.left
                anchors.top: parent.top

                id: headings

                Label {
                    id: idName
                    text: "<b>Name</b>"

                    horizontalAlignment: Text.AlignHCenter
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.margins: 10
                }

                Label {
                    text: "<b>Axes</b>"
                    width: 75
                    anchors.right: idButtons.left
                    anchors.top: parent.top
                    anchors.margins: 10
                }
                Label {
                    id: idButtons
                    text: "<b>Buttons</b>"
                    width: 75
                    horizontalAlignment: Text.AlignHCenter
                    anchors.right: idHats.left
                    anchors.top: parent.top
                    anchors.margins: 10
                }
                Label {
                    id: idHats
                    text: "<b>Hats</b>"
                    width: 75
                    anchors.right: idVid.left
                    anchors.top: parent.top
                    anchors.margins: 10
                }
                Label {
                    id: idVid
                    text: "<b>VID</b>"
                    width: 75
                    anchors.right: idPid.left
                    anchors.top: parent.top
                    anchors.margins: 10
                }
                Label {
                    id: idPid
                    text: "<b>PID</b>"
                    width: 75
                    anchors.right: idGuid.left
                    anchors.top: parent.top
                    anchors.margins: 10
                }
                Label {
                    id: idGuid
                    text: "<b>GUID</b>"
                    width: 315
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.margins: 10
                }
            }
        }
    }
}
