// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Gremlin.Style

Item {
    id: _root

    property string deviceGuid
    property string title

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

            JGText {
                text: title + " - Axes"
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter

                height: 2
                color: Style.lowColor
            }
        }

        ListView {
            id: _list

            Layout.fillWidth: true
            Layout.preferredHeight: 150

            orientation: Qt.Horizontal
            spacing: 10

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
                    width: 60

                    Label {
                        Layout.alignment: Qt.AlignHCenter

                        text: "Axis " +  identifier
                    }
                    BetterProgressBar {
                        Layout.fillHeight: true
                        Layout.alignment: Qt.AlignHCenter

                        orientation: BetterProgressBar.Orientation.Vertical
                        barSize: 20
                        height: 100

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
