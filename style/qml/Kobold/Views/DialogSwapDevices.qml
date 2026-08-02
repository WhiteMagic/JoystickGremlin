// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Templates as T
import QtQuick.Window

import Gremlin.Device
import Gremlin.Profile
import Gremlin.Tools
import Kobold.Foundation

Window {
    id: _root

    width: Metrics.dp(800)
    height: _content.implicitHeight + 3 * Metrics.gapL

    color: Theme.bg

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
        anchors.margins: Metrics.gapL

        RowLayout {
            Label {
                Layout.preferredWidth: Metrics.labelColumn

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
                Layout.preferredWidth: Metrics.labelColumn

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
                delegate: T.ItemDelegate {
                    id: _delegate

                    required property int index
                    required property string name
                    required property string guid

                    width: ListView.view.width
                    height: Metrics.controlHeight
                    highlighted: _physicalDeviceSelection.highlightedIndex === index

                    contentItem: RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: Metrics.gapM
                        anchors.rightMargin: Metrics.gapM
                        spacing: Metrics.gapM

                        Text {
                            Layout.fillWidth: true

                            text: _delegate.name
                            color: Theme.fg
                            font: _physicalDeviceSelection.font
                            elide: Text.ElideRight
                            verticalAlignment: Text.AlignVCenter
                        }

                        Text {
                            text: _delegate.guid
                            color: Theme.fgMuted
                            font.family: FontType.mono
                            font.pixelSize: Metrics.textDetail
                            verticalAlignment: Text.AlignVCenter
                        }
                    }

                    background: Rectangle {
                        color: _delegate.highlighted ? Theme.bgSelected : _delegate.hovered ? Theme.bgHover : "transparent"
                    }
                }
            }
        }

        RowLayout {
            Layout.topMargin: Metrics.gapM

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
                Layout.leftMargin: Metrics.gapM

                text: "Select devices, then click the button."
            }
        }
    }
}
