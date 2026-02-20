// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import QtQuick.Controls.Universal

import Gremlin.Device
import Gremlin.Profile

// Render buttons for all input devices and the logical device as well as the
// scripts and profile settings tabs.
Item {
    id: _root

    property DeviceListModel deviceListModel

    DeviceTabBar {
        id: _deviceList

        anchors.fill: parent

        Component.onCompleted: { itemAt(0).clicked() }

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
            id: _keyboardButton

            text: "Keyboard"
            width: _metricKeyboard.width + 50
            checked: uiState.currentTab === "keyboard"

            onClicked: () => {
                uiState.setCurrentTab("keyboard")
                uiState.setCurrentDevice("6f1d2b61-d5a0-11cf-bfc7-444553540000")
            }

            TextMetrics {
                id: _metricKeyboard

                font: _logicalButton.font
                text: _logicalButton.text
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
