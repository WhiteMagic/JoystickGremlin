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
    minimumWidth: 900
    minimumHeight: 400

    title: "Auto Mapper: Maps your physical controls to vJoy inputs"

    DeviceListModel {
        id: physicalDevices
        deviceType: "physical"
    }

    DeviceListModel {
        id: virtualDevices
        deviceType: "virtual"
    }

    AutoMapper {
        id: autoMapper
    }

    // Properties to track the selected devices and user selections.
    property var selectedPhysicalDevices: ({})
    property var selectedVJoyDevices: ({})
    property bool overwriteNonEmpty: false
    property bool repeatVJoy: false

    property string statusMessage: "Select devices, options and click the Create button"

    Rectangle {
        anchors.fill: parent
        anchors.margins: 10
        
        ColumnLayout {
            anchors.fill: parent
            spacing: 10

            // Description/Manual Section
            TextOutputBox {
                Layout.fillWidth: true
                Layout.preferredHeight: 100
                text: qsTr("<ul>" +
                      "<li>Select source physical devices and target vJoy devices" +
                      "<li>Click 'Create 1:1 mappings' to map from physical to virtual inputs" +
                      "<li>Enable 'Overwrite non-empty' to replace existing mappings in the profile" +
                      "<li>Enable 'Repeat vJoy' to cycle through vJoy inputs, if needed to map all physical inputs" +
                      "</ul>")
            }

            // Main content area with device lists
            RowLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 10

                // Physical Devices Column
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 5

                    GroupBox {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        title: qsTr("Physical Devices")

                        ScrollView {
                            id: _physicalScroll
                            anchors.fill: parent
                            clip: true
                            
                            ListView {
                                model: physicalDevices
                                spacing: 5
                                delegate: CheckBox {
                                    width: ListView.view.width - 10
                                    text: model.name
                                    checked: false
                                    onCheckedChanged: {
                                        selectedPhysicalDevices[model.guid] = checked;
                                    }
                                }
                            }
                        }
                    }

                    Switch {
                        id: _overwriteSwitch
                        Layout.fillWidth: true
                        text: qsTr("Overwrite non-empty physical inputs")

                        ToolTip {
                            visible: parent.hovered
                            text: qsTr("Overwrite non-empty physical inputs")
                            delay: 500
                        }

                        onToggled: function() {
                            overwriteNonEmpty = position ? true : false;
                        }
                    }
                }

                // vJoy Devices Column
                ColumnLayout {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    spacing: 5

                    GroupBox {
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        title: qsTr("vJoy Devices")

                        ScrollView {
                            id: _vjoyScroll
                            anchors.fill: parent
                            clip: true
                            
                            ListView {
                                model: virtualDevices
                                spacing: 5
                                delegate: CheckBox {
                                    width: ListView.view.width - 10
                                    text: model.name
                                    checked: false
                                    onCheckedChanged: {
                                        selectedVJoyDevices[model.vjoy_id] = checked;
                                    }
                                }
                            }
                        }
                    }

                    Switch {
                        id: _repeatSwitch
                        Layout.fillWidth: true
                        text: qsTr("Repeat vJoy devices")

                        ToolTip {
                            visible: parent.hovered
                            text: qsTr("Repeat vJoy devices")
                            delay: 500
                        }

                        onToggled: function() {
                            repeatVJoy = position ? true : false;
                        }
                    }
                }
            }

            // Action bar with button and status
            RowLayout {
                Layout.fillWidth: true
                Layout.preferredHeight: 35
                spacing: 10

                Button {
                    id: _createButton
                    text: qsTr("Create 1:1 mappings")
                    Layout.preferredWidth: implicitWidth + 20
                    Layout.preferredHeight: 30
                    onClicked: {
                        statusMessage = autoMapper.create_mappings(
                            selectedPhysicalDevices, selectedVJoyDevices,
                            overwriteNonEmpty, repeatVJoy);
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
}
