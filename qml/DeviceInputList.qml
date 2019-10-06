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

    property string deviceGuid
    property int inputIndex

    Device {
        id: deviceModel

        guid: deviceGuid
    }

    ScrollView {
        id: scrollView
        anchors.fill: parent

        ListView
        {
            id: inputList
            anchors.fill: parent

            width: parent.width
            model: deviceModel
            delegate: deviceDelegate

            onCurrentIndexChanged: root.inputIndex = currentIndex;

            boundsBehavior: Flickable.StopAtBounds
        }

        Component {
            id: deviceDelegate

            Rectangle {
                id: rect

                width: parent.width
                height: 50

                color: model.index == inputList.currentIndex ? Universal.chromeMediumColor : Universal.background

                MouseArea {
                    anchors.fill: parent
                    onClicked: inputList.currentIndex = model.index
                }

                Label {
                    text: name
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }

}