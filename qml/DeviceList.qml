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


import QtQuick 2.14
import QtQuick.Controls 2.14
import QtQuick.Layouts 1.14
import QtQuick.Window 2.14

import QtQuick.Controls.Universal 2.14

import gremlin.ui.device 1.0


Item {
    id: root

    property int deviceIndex: 0
    property DeviceListModel deviceListModel

    ScrollView {
        id: idScrollView
        anchors.fill: parent

        ListView
        {
            id: idDeviceList
            anchors.fill: parent

            model: deviceListModel
            delegate: idDeviceDelegate

            onCurrentIndexChanged: root.deviceIndex = currentIndex

            boundsBehavior: Flickable.StopAtBounds
        }

        Component {
            id: idDeviceDelegate

            Rectangle {
                id: rect

                implicitHeight: idDeviceName.height
                implicitWidth: idDeviceList.width

                color: model.index == idDeviceList.currentIndex ? Universal.chromeMediumColor : Universal.background

                DisplayText {
                    id: idDeviceName
                    text: name
                    wrapMode: Text.Wrap
                    width: 200
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: idDeviceList.currentIndex = model.index
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