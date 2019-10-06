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

import gremlin.ui.device 1.0


Item {
    id: root
    width: parent.width
//    anchors.top: parent.top
//    anchors.bottom: parent.bottom

    property int deviceIndex: 0
    property DeviceListModel deviceListModel

    ScrollView {
        id: scrollView
        anchors.fill: parent

        ListView
        {
            id: deviceList
            anchors.fill: parent

            width: parent.width
            model: deviceListModel
            delegate: deviceDelegate

            onCurrentIndexChanged: root.deviceIndex = currentIndex

            boundsBehavior: Flickable.StopAtBounds
        }

        Component {
            id: deviceDelegate

            Rectangle {
                id: rect

                width: parent.width
                height: 50

                color: model.index == deviceList.currentIndex ? Universal.chromeMediumColor : Universal.background

                MouseArea {
                    anchors.fill: parent
                    onClicked: deviceList.currentIndex = model.index
                }

                Label {
                    text: name
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }


//            Repeater {
//                id: deviceTabBarRepeater
//                model: deviceData
//
//                TabButton {
//                    text: model.name
//                    onClicked: deviceInput.currentIndex = model.index
//
//                    background: Rectangle {
//                        color: model.index == 0 ? Universal.chromeMediumColor : Universal.background
//                    }
//                }
//            }

//    StackLayout {
//        id: deviceInput
//        currentIndex: 0
//
//        width: parent.width
//        anchors.top: deviceTabBar.bottom
//        anchors.bottom: parent.bottom
//
//        Repeater {
//            id: deviceInputRepeater
//            model: deviceData
//
//            Rectangle {
//                color: "teal"
//                width: 200
//                height: 200
//
//                Text {
//                    text: model.name
//                }
//            }
//        }
//    }
}