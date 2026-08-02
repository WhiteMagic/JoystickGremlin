// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Kobold.Foundation
import Kobold.Controls

Window {
    id: _root

    minimumWidth: Metrics.dp(1000)
    minimumHeight: Metrics.dp(300)

    readonly property int columnAxes:       Metrics.dp(50)
    readonly property int columnButtons:    Metrics.dp(75)
    readonly property int columnHats:       Metrics.dp(50)
    readonly property int columnVid:        Metrics.dp(100)
    readonly property int columnPid:        Metrics.dp(100)
    readonly property int columnJoystickId: Metrics.dp(100)
    readonly property int columnGuid:       Metrics.dp(320)

    color: Theme.bg

    title: "Device Information"

    ColumnLayout {
        anchors.fill: parent

        RowLayout {
            Layout.preferredHeight: Metrics.rowAction
            Layout.rightMargin: _list.scrollBar.width + Metrics.gapM

            HeaderText {
                text: "Name"
                Layout.fillWidth: true
            }
            HeaderText {
                text: "Axes"
                Layout.preferredWidth: _root.columnAxes
                horizontalAlignment: Text.AlignRight
                rightPadding: Metrics.gapL
            }
            HeaderText {
                text: "Buttons"
                Layout.preferredWidth: _root.columnButtons
                horizontalAlignment: Text.AlignRight
                rightPadding: Metrics.gapL
            }
            HeaderText {
                text: "Hats"
                Layout.preferredWidth: _root.columnHats
                horizontalAlignment: Text.AlignRight
                rightPadding: Metrics.gapL
            }
            HeaderText {
                text: "VID"
                Layout.preferredWidth: _root.columnVid
                horizontalAlignment: Text.AlignRight
                rightPadding: Metrics.gapL
            }
            HeaderText {
                text: "PID"
                Layout.preferredWidth: _root.columnPid
                horizontalAlignment: Text.AlignRight
                rightPadding: Metrics.gapL
            }
            HeaderText {
                text: "Joystick ID"
                Layout.preferredWidth: _root.columnJoystickId
                horizontalAlignment: Text.AlignRight
                rightPadding: Metrics.gapL
            }
            HeaderText {
                text: "Device GUID"
                Layout.preferredWidth: _root.columnGuid
            }
        }

        ScrollList {
            id: _list

            Layout.fillWidth: true
            Layout.fillHeight: true

            reuseItems: true
            model: DeviceListModel {}

            delegate: Rectangle {
                id: _outer

                width: _list.width - _list.scrollBar.width
                height: Metrics.rowAction

                color: index % 2 === 0 ? Theme.bgAlt : Theme.bg

                RowLayout {
                    width: parent.width

                    TextEntry {
                        text: name
                        Layout.fillWidth: true
                        Layout.leftMargin: Metrics.gapM
                        horizontalAlignment: Text.AlignLeft
                    }
                    TextEntry {
                        text: axes
                        Layout.preferredWidth: _root.columnAxes
                    }
                    TextEntry {
                        text: buttons
                        Layout.preferredWidth: _root.columnButtons
                    }
                    TextEntry {
                        text: hats
                        Layout.preferredWidth: _root.columnHats
                    }
                    TextEntry {
                        text: vid
                        Layout.preferredWidth: _root.columnVid
                    }
                    TextEntry {
                        text: pid
                        Layout.preferredWidth: _root.columnPid
                    }
                    TextEntry {
                        text: joy_id
                        Layout.preferredWidth: _root.columnJoystickId
                    }
                    TextField {
                        Layout.preferredWidth: _root.columnGuid
                        Layout.rightMargin: Metrics.gapM

                        text: guid

                        horizontalAlignment: Text.AlignHCenter
                        readOnly: true
                    }
                }
            }
        }
    }

    component TextEntry : Label {
        Layout.preferredHeight: Metrics.rowAction

        elide: Text.ElideRight

        horizontalAlignment: Text.AlignRight
        verticalAlignment: Text.AlignVCenter
        rightPadding: Metrics.gapL
    }

    component HeaderText : Label {
        Layout.preferredHeight: Metrics.rowAction

        font.weight: FontType.semiBold

        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }
}
