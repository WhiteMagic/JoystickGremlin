// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Gremlin.UI
import Kobold.Controls
import Kobold.Foundation

// Visualizes the current state of a device's axes through a set of bars that indicate
// the current value of each axis. This is used in the input viewer tool.
Item {
    id: _root

    property string deviceGuid
    property string title

    readonly property int axisColumnWidth: Metrics.dp(60)
    readonly property int axisBarHeight:   Metrics.dp(100)
    readonly property int axisBarSize:     Metrics.dp(20)

    readonly property DeviceAxisState _axisState: ModelFactory.deviceAxisState(_root)

    implicitHeight: _content.implicitHeight

    Component.onCompleted: () => { _axisState.guid = deviceGuid }

    function formatPercentage(value)
    {
        return Math.round(value * 100)
    }

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        RowLayout {
            id: _header

            Label {
                text: title + " - Axes"
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter

                height: 2 * Metrics.hairline
                color: Theme.line
            }
        }

        ListView {
            id: _list

            Layout.fillWidth: true
            Layout.preferredHeight: Metrics.dp(150)

            orientation: Qt.Horizontal
            spacing: Metrics.gapM

            boundsMovement: Flickable.StopAtBounds
            boundsBehavior: Flickable.StopAtBounds
            interactive: false

            model: _root._axisState
            delegate: Component {
                ColumnLayout {
                    required property int index
                    required property int identifier
                    required property double value

                    height: ListView.view.height
                    width: _root.axisColumnWidth

                    Label {
                        Layout.alignment: Qt.AlignHCenter

                        text: "Axis " +  identifier
                    }
                    ProgressBar {
                        Layout.fillHeight: true
                        Layout.alignment: Qt.AlignHCenter

                        orientation: Qt.Vertical
                        barSize: _root.axisBarSize
                        height: _root.axisBarHeight

                        from: -1
                        to: 1
                        value: parent.value
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter

                        text: formatPercentage(value) + " %"
                    }

                }
            }
        }
    }

}
