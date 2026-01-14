// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Gremlin.Profile
import Gremlin.Style
import Gremlin.Tools

Window {
    width: 800
    height: _content.implicitHeight + 30

    color: Style.background
    Universal.theme: Style.theme

    title: "Swap Devices"

    DeviceListModel {
        id: _physicalDevices

        deviceType: "physical"
    }

    ProfileDeviceListModel {
        id: _profileDevices
    }

    Tools {
        id: _tools
    }


    ColumnLayout {
        id: _content

        anchors.fill: parent
        anchors.margins: 10

        RowLayout {
            Label {
                Layout.preferredWidth: 200

                text: "From profile device"
                font.bold: true
            }

            ComboBox {
                id: _profileDeviceSelection

                Layout.fillWidth: true

                model: _profileDevices

                textRole: "nameAndActions"
                valueRole: "uuid"
            }
        }

        RowLayout {
            Label {
                Layout.preferredWidth: 200

                text: "To connected device"
                font.bold: true
            }

            ComboBox {
                id: _physicalDeviceSelection

                Layout.fillWidth: true

                model: _physicalDevices

                textRole: "name"
                valueRole: "guid"

                displayText: currentText + " : " + currentValue
                delegate: ItemDelegate {
                    text: model.name + " : " + model.guid

                    width: ListView.view.width
                    font.weight: control.currentIndex === index ? Font.DemiBold : Font.Normal
                    highlighted: control.highlightedIndex === index
                }
            }
        }

        RowLayout {
            Layout.topMargin: 10

            Button {
                text: "Swap Bindings"
                onClicked: () => {
                    _statusMessage.text = _tools.swapDevices(
                        _profileDeviceSelection.currentValue,
                        _physicalDeviceSelection.currentValue
                    )
                }
            }

            Label {
                id: _statusMessage

                Layout.fillWidth: true
                Layout.leftMargin: 10

                text: "Select devices, then click the button."
            }
        }
    }
}
