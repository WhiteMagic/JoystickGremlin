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
import Gremlin.UI


Window {
    id: _root

    minimumWidth: 900
    minimumHeight: 300

    title: "Auto Mapper"

    DeviceListModel {
        id: physicalDevices
        deviceType: "physical"
    }

    DeviceListModel {
        id: virtualDevices
        deviceType: "virtual"
    }

    property AutoMapper autoMapper: backend.getAutoMapper()

    // Properties to track the selected devices
    property var selectedPhysicalDevices: ({})
    property var selectedVJoyDevices: ({})
    property bool overwriteNonEmpty: false
    property bool repeatVJoy: false

    Rectangle {
        id: mainWindow
        anchors.fill: parent
        anchors.margins: 10
        
        Column {
            id: mainColumn
            anchors.fill: parent
            spacing: 10

            Row {
                id: devicesRow
                width: parent.width
                height: parent.height - 60 // Leave space for the button
                spacing: 20

                Column {
                    id: physicalDevicesColumn
                    width: parent.width * 0.45
                    height: parent.height
                    spacing: 5

                    CheckBox {
                        id: overwriteNonEmptyPhysicalInputsCheckbox
                        width: parent.width
                        text: qsTr("Overwrite non-empty physical inputs")
                        checked: overwriteNonEmpty
                        onCheckedChanged: overwriteNonEmpty = checked
                    }

                    GroupBox {
                        id: physicalDevicesGroupBox
                        width: parent.width
                        height: parent.height - overwriteNonEmptyPhysicalInputsCheckbox.height - 5
                        title: qsTr("Physical Devices")

                        ScrollView {
                            id: physicalDevicesScroll
                            anchors.fill: parent
                            clip: true
                            
                            Column {
                                width: physicalDevicesScroll.width - 20
                                spacing: 5
                                padding: 5
                                
                                Repeater {
                                    model: physicalDevices
                                    delegate: CheckBox {
                                        width: parent.width - 10
                                        text: model.name
                                        checked: false
                                        onCheckedChanged: {
                                            selectedPhysicalDevices[model.guid] = checked;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                Column {
                    id: vjoyDevicesColumn
                    width: parent.width * 0.45
                    height: parent.height
                    spacing: 5

                    CheckBox {
                        id: repeatVJoyCheckbox
                        width: parent.width
                        text: qsTr("Repeat vJoy devices")
                        checked: repeatVJoy
                        onCheckedChanged: repeatVJoy = checked
                    }

                    GroupBox {
                        id: vjoyDevicesGroupBox
                        width: parent.width
                        height: parent.height - repeatVJoyCheckbox.height - 5
                        title: qsTr("vJoy Devices")

                        ScrollView {
                            id: vjoyDevicesScroll
                            anchors.fill: parent
                            clip: true
                            
                            Column {
                                width: vjoyDevicesScroll.width - 20
                                spacing: 5
                                padding: 5
                                
                                Repeater {
                                    model: virtualDevices
                                    delegate: CheckBox {
                                        width: parent.width - 10
                                        text: model.name
                                        checked: false
                                        onCheckedChanged: {
                                            selectedVJoyDevices[model.vjoy_id] = checked;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Row {
                id: buttonRow
                width: Math.min(600, parent.width * 0.8)
                height: 60
                spacing: 10
                anchors.horizontalCenter: parent.horizontalCenter

                Button {
                    id: createButton
                    text: qsTr("Create 1:1 mappings")
                    onClicked: {
                        var result = autoMapper.create_mappings(
                            selectedPhysicalDevices, selectedVJoyDevices,
                            overwriteNonEmpty, repeatVJoy);
                        resultText.text = result ? result : "";
                    }
                    height: parent.height
                    width: 200
                }

                TextArea {
                    id: resultText
                    width: parent.width - createButton.width - parent.spacing
                    height: parent.height
                    readOnly: true
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignRight
                    placeholderText: qsTr("Awaiting user selections and button press")
                    background: Rectangle {
                        color: "#f5f5f5"
                        border.color: "#cccccc"
                        border.width: 1
                        radius: 2
                    }
                }
            }
        }
    }
}
