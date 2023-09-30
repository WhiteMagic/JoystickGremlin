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
import Gremlin.Profile


// ListView item customized to render DeviceListModel instances as a set
// of horizontal tabs
Item {
    id: _root

    property DeviceListModel deviceListModel
    property string deviceGuid: deviceListModel.guidAtIndex(0)
    property alias selectedIndex: _deviceList.currentIndex

    // List view of all inputs present on the currently active device
    ListView {
        id: _deviceList
        anchors.fill: parent
        orientation: ListView.Horizontal

        model: deviceListModel
        delegate: _deviceDelegate

        // Make it behave like a sensible scrolling container
        ScrollBar.vertical: ScrollBar {}
        flickableDirection: Flickable.VerticalFlick
        boundsBehavior: Flickable.StopAtBounds
    }

    // Display name of the device and change background based on the
    // selection state of the device
    Component {
        id: _deviceDelegate

        Label {
            text: name
            leftPadding: 20
            rightPadding: 20
            topPadding: 10
            bottomPadding: 10

            background: Rectangle {
                color: model.index == _deviceList.currentIndex
                    ? Universal.chromeMediumColor : Universal.background
            }

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    _deviceList.currentIndex = model.index
                    _root.deviceGuid = model.guid
                }
            }
        }
    } // Component
} // Item