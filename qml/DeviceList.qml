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
// Logical Device tab
Item {
    id: _root

    property DeviceListModel deviceListModel

    DeviceTabBar {
        id: _deviceList

        anchors.fill: parent

        Component.onCompleted: {
            currentIndex: 0
        }

        Repeater {
            id: _physicalInputs
            model: deviceListModel

            JGTabButton {
                id: _button

                text: name
                width: _metric.width + 50
                checked: uiState.currentTab === "physical" &&
                    uiState.currentDevice === model.guid

                onClicked: () => {
                    uiState.setCurrentTab("physical")
                    uiState.setCurrentDevice(model.guid)
                }

                TextMetrics {
                    id: _metric

                    font: _button.font
                    text: _button.text
                }
            }
        }

        JGTabButton {
            id: _logicalButton

            text: "Logical Device"
            width: _metricIO.width + 50
            checked: uiState.currentTab === "logical"

            onClicked: () => {
                uiState.setCurrentTab("logical")
                uiState.setCurrentDevice("f0af472f-8e17-493b-a1eb-7333ee8543f2")
            }

            TextMetrics {
                id: _metricIO

                font: _logicalButton.font
                text: _logicalButton.text
            }
        }

        // Empty item to push the script tab to the right
        JGTabButton {
            Layout.fillWidth: true
            height: 0
        }

        JGTabButton {
            id: _scriptButton

            text: "Scripts"
            width: _metricScripts.width + 50
            checked: uiState.currentTab === "scripts"

            onClicked: () => { uiState.setCurrentTab("scripts") }

            TextMetrics {
                id: _metricScripts

                font: _scriptButton.font
                text: _scriptButton.text
            }
        }

        JGTabButton {
            id: _profileSettingsButton

            text: "Settings"
            width: _metricProfileSettings.width + 50
            checked: uiState.currentTab === "settings"

            onClicked: () => { uiState.setCurrentTab("settings") }

            TextMetrics {
                id: _metricProfileSettings

                font: _profileSettingsButton.font
                text: _profileSettingsButton.text
            }
        }

    }
}