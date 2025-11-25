// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2025 Lionel Ott
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
import Gremlin.Tools


Window {
    minimumWidth: 900
    minimumHeight: 300

    title: "Swap devices: Swaps bindings between two devices"

    DeviceListModel {
        id: physicalDevices
        deviceType: "physical"
    }

    ProfileDeviceListModel {
        id: profileDevices
    }

    Tools {
        id: tools
    }

    property string statusMessage: "Select devices, and click the Swap Bindings button"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10

        // Description/Manual Section
        TextOutputBox {
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            text: qsTr("<ul>" +
                    "<li>Select the devices to swap bindings between" +
                    "<li>Click 'Swap' to swap the bindings between the selected devices" +
                    "<li>Resulting bindings may be invalid if devices have different numbers " +
                    "of inputs" +
                    "</ul>")
        }

        // Main content area with device dropdowns.
        RowLayout {
            spacing: 10

            // First ("Connected") Device Column
            ColumnLayout {
                Label {
                    text: qsTr("Select connected device")
                    font.bold: true
                }
                
                ComboBox {
                    id: firstDeviceCombo
                    model: physicalDevices
                    textRole: "name"
                    Layout.fillWidth: true
                    onActivated: physicalDevices.selectedIndex = currentIndex
                    Component.onCompleted: physicalDevices.selectedIndex = currentIndex
                }
            }

            // Second ("Profile") Device Column
            ColumnLayout {
                Label {
                    text: qsTr("Select device in profile")
                    font.bold: true
                }
                
                ComboBox {
                    model: profileDevices
                    textRole: "uuid"
                    Layout.fillWidth: true
                    onActivated: profileDevices.selectedIndex = currentIndex
                    Component.onCompleted: profileDevices.selectedIndex = currentIndex

                    delegate: ItemDelegate {
                        width: parent.width
                        text: `${model.name || model.uuid}: ${model.numBindings} ${model.numBindings === 1 ? 'binding' : 'bindings'}`
                    }
                }
            }
        }

        // Action bar with button and status
        RowLayout {
            spacing: 10

            Button {
                id: _swapButton
                text: qsTr("Swap Bindings")
                onClicked: {
                    statusMessage = tools.swapDevices(
                        profileDevices.uuidAtIndex(profileDevices.selectedIndex),
                        physicalDevices.uuidAtIndex(physicalDevices.selectedIndex));
                }
            }

            TextOutputBox {
                id: _statusNotification
                Layout.fillWidth: true
                Layout.preferredHeight: 30
                text: statusMessage
            }
        }
    }
}
