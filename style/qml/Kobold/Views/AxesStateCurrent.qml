// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Kobold.Controls
import Kobold.Foundation

Item {
    id: _root

    property string deviceGuid
    property string title

    // Local to this file -- single consumer, not a shared design concept.
    readonly property int axisColumnWidth: Metrics.dp(60)
    readonly property int axisBarHeight:   Metrics.dp(100)
    readonly property int axisBarSize:     Metrics.dp(20)

    implicitHeight: _content.implicitHeight

    function format_percentage(value)
    {
        return Math.round(value * 100)
    }

    DeviceAxisState {
        id: _axis_state

        guid: deviceGuid
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

            model: _axis_state
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
                    BetterProgressBar {
                        Layout.fillHeight: true
                        Layout.alignment: Qt.AlignHCenter

                        orientation: BetterProgressBar.Orientation.Vertical
                        barSize: _root.axisBarSize
                        height: _root.axisBarHeight

                        from: -1
                        to: 1
                        value: parent.value
                    }
                    Label {
                        Layout.alignment: Qt.AlignHCenter

                        text: format_percentage(value) + " %"
                    }

                }
            }
        }
    }

}
