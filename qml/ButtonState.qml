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

    function computeButtonHeight() {
        let columns =  Math.floor(
            Math.max(_button_grid.width, _button_grid.Layout.minimumWidth) /
            _button_grid.cellWidth
        )
        let rows = Math.ceil(_button_grid.count / columns)
        return rows * _button_grid.cellHeight
    }

    function computeHatHeight(cellHeight) {
        return Math.ceil(_hat_grid.count / 2) * cellHeight
    }

    DeviceButtonState {
        id: _button_state

        guid: deviceGuid
    }

    DeviceHatState {
        id: _hat_state

        guid: deviceGuid
    }

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        RowLayout {
            id: _header

            JGText {
                text: title + " - Buttons & Hats"
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter

                height: 2
                color: Style.lowColor
            }
        }

        RowLayout {
            // Button state display.
            GridView {
                id: _button_grid

                Layout.fillWidth: true
                Layout.minimumWidth: 400
                Layout.preferredWidth: 600
                Layout.minimumHeight: computeButtonHeight(_root.width)
                Layout.alignment: Qt.AlignTop

                boundsMovement: Flickable.StopAtBounds
                boundsBehavior: Flickable.StopAtBounds
                interactive: false

                cellWidth: 50
                cellHeight: 50

                model: _button_state
                delegate: Component {
                    RoundButton {
                        required property int index
                        required property int identifier
                        required property bool value

                        width: 40
                        height: 40
                        radius: 10

                        hoverEnabled: false

                        text: identifier
                        checked: value
                        font.pointSize: 10
                    }
                }
            }

            // Hat state display.
            GridView {
                id: _hat_grid

                Layout.fillWidth: true
                Layout.minimumWidth: 200
                Layout.preferredWidth: 200
                Layout.minimumHeight: computeHatHeight(cellHeight)
                Layout.alignment: Qt.AlignTop

                boundsMovement: Flickable.StopAtBounds
                boundsBehavior: Flickable.StopAtBounds

                cellWidth: 100
                cellHeight: 100

                model: _hat_state
                delegate: Component {
                    HatView {
                        required property int identifier
                        required property point value

                        height: _hat_grid.cellHeight - 20
                        width: _hat_grid.cellWidth - 20

                        text: identifier
                        currentValue: value
                    }
                }
            }
        }
    }

}
