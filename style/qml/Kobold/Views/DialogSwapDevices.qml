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
import Gremlin.UI
import Kobold.Foundation

Window {
    id: _root

    width: Metrics.dp(800)
    height: _content.implicitHeight + 3 * Metrics.gapL

    color: Theme.bg

    title: "Swap Devices"

    readonly property DeviceListModel _physicalDevices:
        ModelFactory.deviceListModel(_root, "physical")
    readonly property ProfileDeviceListModel _profileDevices:
        ModelFactory.profileDeviceListModel(_root)
    readonly property Tools _tools: ModelFactory.tools(_root)

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

                model: _root._profileDevices

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

                model: _root._physicalDevices

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

                        Label {
                            Layout.fillWidth: true

                            text: _delegate.name
                            font: _physicalDeviceSelection.font
                            elide: Text.ElideRight
                            verticalAlignment: Text.AlignVCenter
                        }

                        Label {
                            text: _delegate.guid
                            color: Theme.fgMuted
                            font.family: FontType.mono
                            font.pixelSize: Metrics.textDetail
                            verticalAlignment: Text.AlignVCenter
                        }
                    }

                    background: Rectangle {
                        color: _delegate.highlighted
                                ? Theme.bgSelected
                                    : _delegate.hovered ? Theme.bgHover : "transparent"
                    }
                }
            }
        }

        RowLayout {
            Layout.topMargin: Metrics.gapM

            Label {
                id: _statusMessage

                Layout.fillWidth: true
                Layout.rightMargin: Metrics.gapM

                text: "Select devices, then click the button."
                horizontalAlignment: Text.AlignRight
            }

            Button {
                text: "Swap Bindings"
                onClicked: () => {
                    _statusMessage.text = _root._tools.swapDevices(
                        _profileDeviceSelection.currentValue,
                        _physicalDeviceSelection.currentValue
                    )
                }
            }
        }
    }
}
