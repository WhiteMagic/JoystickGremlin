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
    property alias currentIndex: _deviceList.currentIndex
    property alias count: _deviceList.count

    DeviceTabBar {
        id: _deviceList

        anchors.fill: parent

        Component.onCompleted: { itemAt(0).clicked() }

        // Show joystick devices used as inputs.
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

        // Keyboard and logical device buttons.
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

                font: _keyboardButton.font
                text: _keyboardButton.text
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
    }
}
