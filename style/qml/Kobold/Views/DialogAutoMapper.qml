// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Gremlin.Profile
import Gremlin.Tools
import Kobold.Controls
import Kobold.Foundation

Window {
    minimumWidth: Metrics.dp(900)
    minimumHeight: Metrics.dp(400)

    color: Theme.bg

    title: "Auto Mapper"

    DeviceListModel {
        id: _physicalDevices
        deviceType: "physical"
    }

    DeviceListModel {
        id: _virtualDevices
        deviceType: "virtual"
    }

    Tools {
        id: tools
    }

    // Properties to track the selected devices and user selections.
    property var selectedPhysicalDevices: ({})
    property var selectedVJoyDevices: ({})

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.gapL

        RowLayout {
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.rightMargin: Metrics.gapM

                RowLayout {
                    Label {
                        text: "Physical Devices"
                    }

                    Spacer {
                        Layout.preferredHeight: 1
                        color: Theme.line
                    }
                }

                ScrollList {
                    Layout.fillHeight: true
                    Layout.fillWidth: true

                    model: _physicalDevices
                    scrollbarAlwaysVisible: true

                    delegate: CheckBox {
                        width: ListView.view.width - Metrics.gapM

                        text: model.name
                        checked: false

                        onCheckedChanged: () => {
                            selectedPhysicalDevices[model.guid] = checked
                        }
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true

                RowLayout {
                    Label {
                        text: "vJoy Devices"
                    }

                    Spacer {
                        Layout.preferredHeight: 1
                        color: Theme.line
                    }
                }

                ScrollList {
                    Layout.fillWidth: true
                    Layout.fillHeight: true

                    model: _virtualDevices
                    scrollbarAlwaysVisible: true

                    delegate: CheckBox {
                        width: ListView.view.width - Metrics.gapM

                        text: model.name
                        checked: false

                        onCheckedChanged: () => {
                            selectedVJoyDevices[model.vjoy_id] = checked
                        }
                    }
                }
            }
        }

        RowLayout {
            Label {
                text: "Select Mode"
            }

            ComboBox {
                id: _modeSelector

                model: ModeListModel {}

                textRole: "name"
            }

            Spacer {}

            Switch {
                id: _overwriteNonEmpty

                text: "Overwrite non-empty physical inputs"

                onToggled: () => { overwriteNonEmpty = checked }
            }

            Switch {
                id: _repeatDevices

                text: "Repeat vJoy devices"

                onToggled: () => { repeatVJoy = checked }
            }
        }

        RowLayout {
            Layout.topMargin: Metrics.gapM

            Button {
                text: "Create 1:1 mappings"

                onClicked: () => {
                    _statusMessage.text = tools.createMappings(
                        _modeSelector.currentText,
                        selectedPhysicalDevices,
                        selectedVJoyDevices,
                        _overwriteNonEmpty.checked,
                        _repeatDevices.checked
                    )

                    selectedPhysicalDevices = ({})
                    selectedVJoyDevices = ({})
                }
            }

            Label {
                id: _statusMessage

                Layout.fillWidth: true
                Layout.leftMargin: Metrics.gapM
                Layout.rightMargin: Metrics.gapM

                text: "Select devices, options and then click the button."
            }

            ToolButton {
                icon.name: "help"

                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: "- Select mode to create bindings in.
- Select source physical devices and target vJoy devices.
- Click \"Create 1:1 mappings\" button.

Overwrite non-empty: Replaces existing mappings in the profile.
Repeat vJoy: Cycles through vJoy inputs, if needed to map all physical inputs."
            }
        }
    }
}
