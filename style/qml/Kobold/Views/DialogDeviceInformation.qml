// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Kobold.Foundation

Window {
    minimumWidth: 1000
    minimumHeight: 300

    color: Theme.bg

    title: "Device Information"

    ColumnLayout {
        anchors.fill: parent

        RowLayout {
            Layout.preferredHeight: 50

            HeaderText {
                text: "Name"
                Layout.fillWidth: true
            }
            HeaderText {
                text: "Axes"
                Layout.preferredWidth: 50
            }
            HeaderText {
                text: "Buttons"
                Layout.preferredWidth: 75
            }
            HeaderText {
                text: "Hats"
                Layout.preferredWidth: 50
            }
            HeaderText {
                text: "VID"
                Layout.preferredWidth: 100
            }
            HeaderText {
                text: "PID"
                Layout.preferredWidth: 100
            }
            HeaderText {
                text: "Joystick ID"
                Layout.preferredWidth: 100
            }
            HeaderText {
                text: "Device GUID"
                Layout.preferredWidth: 320
            }
        }

        ScrollView {
            id: _view

            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                spacing: 0

                Repeater {
                    model: DeviceListModel {}

                    delegate: Rectangle {
                        id: _outer

                        height: Metrics.rowCompact
                        width: _view.width

                        color: index % 2 === 0 ? Theme.bgAlt : Theme.bg

                        RowLayout {
                            width: parent.width

                            TextEntry {
                                text: name
                                Layout.fillWidth: true
                                Layout.leftMargin: 10
                                horizontalAlignment: Text.AlignLeft

                                ToolTip {
                                    text: parent.text
                                    width: contentWidth > 500 ? 500 : contentWidth + 20
                                    visible: _hoverHandler.hovered
                                    delay: 500
                                }

                                HoverHandler {
                                    id: _hoverHandler
                                    acceptedDevices: PointerDevice.Mouse |
                                        PointerDevice.TouchPad
                                }

                            }
                            TextEntry {
                                text: axes
                                Layout.preferredWidth: 50
                            }
                            TextEntry {
                                text: buttons
                                Layout.preferredWidth: 75
                            }
                            TextEntry {
                                text: hats
                                Layout.preferredWidth: 50
                            }
                            TextEntry {
                                text: vid
                                Layout.preferredWidth: 100
                            }
                            TextEntry {
                                text: pid
                                Layout.preferredWidth: 100
                            }
                            TextEntry {
                                text: joy_id
                                Layout.preferredWidth: 100
                            }
                            TextField {
                                Layout.preferredWidth: 320
                                Layout.rightMargin: 10

                                text: guid

                                horizontalAlignment: Text.AlignHCenter
                                readOnly: true
                            }
                        }
                    }
                }
            }
        }
    }

    component TextEntry : Label {
        Layout.preferredHeight: 40

        elide: Text.ElideRight

        horizontalAlignment: Text.AlignRight
        verticalAlignment: Text.AlignVCenter
        rightPadding: Metrics.gapL
    }

    component HeaderText : Label {
        Layout.preferredHeight: 40

        font.weight: FontType.semiBold

        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
