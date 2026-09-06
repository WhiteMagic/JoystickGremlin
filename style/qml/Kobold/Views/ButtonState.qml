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
    readonly property int buttonSize:   Metrics.dp(40)
    readonly property int buttonRadius: Metrics.even(10)

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

            Label {
                text: title + " - Buttons & Hats"
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter

                height: 2 * Metrics.hairline
                color: Theme.line
            }
        }

        RowLayout {
            // Button state display.
            GridView {
                id: _button_grid

                Layout.fillWidth: true
                Layout.minimumWidth: Metrics.dp(400)
                Layout.preferredWidth: Metrics.dp(600)
                Layout.minimumHeight: computeButtonHeight(_root.width)
                Layout.alignment: Qt.AlignTop

                boundsMovement: Flickable.StopAtBounds
                boundsBehavior: Flickable.StopAtBounds
                interactive: false

                cellWidth: Metrics.dp(50)
                cellHeight: Metrics.dp(50)

                model: _button_state
                delegate: Component {
                    // A readout, not a control -- nothing here is clickable, so it is a
                    // plain rectangle rather than a Button the user cannot press.
                    Rectangle {
                        id: _button

                        required property int index
                        required property int identifier
                        required property bool value

                        width: _root.buttonSize
                        height: _root.buttonSize
                        radius: _root.buttonRadius

                        color: Theme.bgAlt
                        border.width: Metrics.hairline
                        border.color: value ? Theme.accent : Theme.line

                        Label {
                            anchors.centerIn: parent

                            text: _button.identifier
                            font.pixelSize: Metrics.textDetail
                            color: _button.value ? Theme.accent : Theme.fg
                        }
                    }
                }
            }

            // Hat state display.
            GridView {
                id: _hat_grid

                Layout.fillWidth: true
                Layout.minimumWidth: Metrics.dp(200)
                Layout.preferredWidth: Metrics.dp(200)
                Layout.minimumHeight: computeHatHeight(cellHeight)
                Layout.alignment: Qt.AlignTop

                boundsMovement: Flickable.StopAtBounds
                boundsBehavior: Flickable.StopAtBounds

                cellWidth: Metrics.dp(100)
                cellHeight: Metrics.dp(100)

                model: _hat_state
                delegate: Component {
                    HatView {
                        required property int identifier
                        required property point value

                        height: _hat_grid.cellHeight - Metrics.gapL
                        width: _hat_grid.cellWidth - Metrics.gapL

                        text: identifier
                        currentValue: value
                    }
                }
            }
        }
    }

}
