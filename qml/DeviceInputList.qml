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

    property string deviceGuid
    property int inputIndex
    property InputIdentifier inputIdentifier

    Device {
        id: idDeviceModel

        guid: deviceGuid
    }

    ScrollView {
        id: scrollView
        anchors.fill: parent

        ListView
        {
            id: idInputList
            anchors.fill: parent

            width: parent.width
            model: idDeviceModel
            delegate: idDeviceDelegate

            onCurrentIndexChanged: {
                root.inputIdentifier = idDeviceModel.inputIdentifier(currentIndex);
                root.inputIndex = currentIndex;
            }

            boundsBehavior: Flickable.StopAtBounds
        }

        Component {
            id: idDeviceDelegate

            Rectangle {
                id: rect

                width: parent.width
                height: 50

                color: model.index == idInputList.currentIndex ? Universal.chromeMediumColor : Universal.background

                MouseArea {
                    anchors.fill: parent
                    // Change selected index as well as set the input item model
                    onClicked: {
                        idInputList.currentIndex = model.index;
//                        inputIdentifier = idDeviceModel.input_identifier(model.index);
//                        console.log(idDeviceModel.input_identifier(model.index));
                    }
                }

                Label {
                    text: name
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }

}