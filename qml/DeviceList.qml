// -*- coding: utf-8; -*-
//
// Copyright (C) 2019 Lionel Ott
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


// Render all detected devices using a TabBar while also displaying the
// Intermediate output tab
Item {
    id: _root

    property DeviceListModel deviceListModel
    property string deviceGuid: deviceListModel.guidAtIndex(0)
    property alias currentIndex: _deviceList.currentIndex

    DeviceTabBar {
        id: _deviceList

        anchors.fill: parent

        Repeater {
            id: _physicalInputs
            model: deviceListModel

            JGTabButton {
                id: _button

                text: name

                width: _metric.width + 50

                onClicked: function() {
                    _deviceList.currentIndex = model.index
                    _root.deviceGuid = Qt.binding(
                        function() { return model.guid }
                    )
                    showIntermediateOutput(false)
                }

                TextMetrics {
                    id: _metric

                    font: _button.font
                    text: _button.text
                }
            }
        }

        JGTabButton {
            id: _ioButton

            text: "Intermediate Output"
            width: _metricIO.width + 50

            onClicked: function() {
                showIntermediateOutput(true)
            }

            TextMetrics {
                id: _metricIO

                font: _ioButton.font
                text: _ioButton.text
            }
        }
    }
}