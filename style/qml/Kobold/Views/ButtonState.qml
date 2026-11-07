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

// Visualizes the state of a device's buttons and hats inside the input viewer tool.
Item {
    id: _root

    property string deviceGuid
    property string title

    readonly property int buttonSize:   Metrics.dp(40)
    readonly property int buttonRadius: Metrics.even(10)
    readonly property int minimumVisibleDuration: 100

    readonly property DeviceButtonState _buttonState: ModelFactory.deviceButtonState(_root)
    readonly property DeviceHatState _hatState: ModelFactory.deviceHatState(_root)

    implicitHeight: _content.implicitHeight

    Component.onCompleted: () => {
        _buttonState.guid = deviceGuid
        _hatState.guid = deviceGuid
    }

    function computeButtonHeight() {
        let columns =  Math.floor(
            Math.max(_buttonGrid.width, _buttonGrid.Layout.minimumWidth) /
            _buttonGrid.cellWidth
        )
        let rows = Math.ceil(_buttonGrid.count / columns)
        return rows * _buttonGrid.cellHeight
    }

    function computeHatHeight(cellHeight) {
        return Math.ceil(_hatGrid.count / 2) * cellHeight
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
                id: _buttonGrid

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

                model: _root._buttonState
                delegate: Component {
                    Rectangle {
                        id: _button

                        required property int index
                        required property int identifier
                        required property bool value

                        // Keeps taps shorter than a frame visible.
                        readonly property bool showPressed:
                            value || _minimumPressDisplay.running

                        width: _root.buttonSize
                        height: _root.buttonSize
                        radius: _root.buttonRadius

                        color: Theme.bgAlt
                        border.width: Metrics.hairline
                        border.color: showPressed ? Theme.accent : Theme.line

                        onValueChanged: () => {
                            if (value) {
                                _minimumPressDisplay.restart()
                            }
                        }

                        Timer {
                            id: _minimumPressDisplay

                            interval: _root.minimumVisibleDuration
                        }

                        Label {
                            anchors.centerIn: parent

                            text: _button.identifier
                            font.pixelSize: Metrics.textDetail
                            color: _button.showPressed ? Theme.accent : Theme.fg
                        }
                    }
                }
            }

            // Hat state display.
            GridView {
                id: _hatGrid

                Layout.fillWidth: true
                Layout.minimumWidth: Metrics.dp(200)
                Layout.preferredWidth: Metrics.dp(200)
                Layout.minimumHeight: computeHatHeight(cellHeight)
                Layout.alignment: Qt.AlignTop

                boundsMovement: Flickable.StopAtBounds
                boundsBehavior: Flickable.StopAtBounds

                cellWidth: Metrics.dp(100)
                cellHeight: Metrics.dp(100)

                model: _root._hatState
                delegate: Component {
                    HatView {
                        required property int identifier
                        required property point value

                        // Keeps changes shorter than a frame visible.
                        property point heldDirection

                        height: _hatGrid.cellHeight - Metrics.gapL
                        width: _hatGrid.cellWidth - Metrics.gapL

                        text: identifier
                        currentValue:
                            value.x === 0 && value.y === 0
                                && _minimumHatDisplay.running
                            ? heldDirection
                            : value

                        onValueChanged: () => {
                            if (value.x !== 0 || value.y !== 0) {
                                heldDirection = value
                                _minimumHatDisplay.restart()
                            }
                        }

                        Timer {
                            id: _minimumHatDisplay

                            interval: _root.minimumVisibleDuration
                        }
                    }
                }
            }
        }
    }

}
