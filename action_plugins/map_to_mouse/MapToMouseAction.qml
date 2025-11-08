// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2024 Lionel Ott
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.


import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import QtQuick.Controls.Universal

import Gremlin.Profile
import Gremlin.ActionPlugins
import "../../qml"


Item {
    id: _root

    property MapToMouseModel action

    property int limitLow: 0
    property int limitHigh: 1000

    implicitHeight: _content.height

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        RowLayout {
            Label {
                id: _label

                Layout.preferredWidth: 50

                text: "<B>Mode</B>"
            }

            // Radio buttons to select the desired mapping mode
            RadioButton {
                id: _mode_button

                text: "Button"
                visible: inputBinding.behavior === "button"

                checked: _root.action.mode === "Button"
                onClicked: function () {
                    _root.action.mode = "Button"
                }

            }

            RadioButton {
                id: _mode_motion

                Layout.fillWidth: true

                text: "Motion"

                checked: _root.action.mode === "Motion"
                onClicked: function () {
                    _root.action.mode = "Motion"
                }
            }
        }

        // Button configuration
        RowLayout {
            visible: _mode_button.checked

            Label {
                text: "Mouse Button"
            }

            InputListener {
                callback: (inputs) => { _root.action.updateInputs(inputs) }
                multipleInputs: false
                eventTypes: ["mouse"]

                buttonLabel: _root.action.button
            }

        }

        // Motion configuration for button-like inputs
        GridLayout {
            visible: _mode_motion.checked && inputBinding.behavior === "button"

            columns: 5

            Label {
                Layout.fillWidth: true

                text: "Minimum speed"
            }

            SpinBox {
                id: _min_speed_button

                Layout.fillWidth: true

                value: _root.action.minSpeed
                from: limitLow
                to: _max_speed_button.value
                editable: true

                onValueModified: function() {
                    _root.action.minSpeed = value
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.horizontalStretchFactor: 1
            }

            Label {
                Layout.fillWidth: true

                text: "Maximum speed"
            }

            SpinBox {
                id: _max_speed_button

                Layout.fillWidth: true

                value: _root.action.maxSpeed
                from: _min_speed_button.value
                to: limitHigh
                editable: true

                onValueModified: function() {
                    _root.action.maxSpeed = value
                }
            }

            Label {
                text: "Time to maximum speed"
            }

            FloatSpinBox {
                minValue: 0
                maxValue: 30
                value: _root.action.timeToMaxSpeed
                stepSize: 1.0
                decimals: 1

                onValueModified: (newValue) => {
                    _root.action.timeToMaxSpeed = newValue
                }
            }

            Rectangle {}

            Label {
                text: "Direction"
            }

            SpinBox {
                value: _root.action.direction
                from: 0
                to: 360
                stepSize: 15
                editable: true

                onValueModified: function() {
                    _root.action.direction = value
                }
            }
        }

        // Motion configuration for axis inputs
        GridLayout {
            visible: _mode_motion.checked && inputBinding.behavior === "axis"

            columns: 4

            Label {
                Layout.fillWidth: true

                text: "Control"
            }

            RadioButton {
                Layout.fillWidth: true

                text: "X Axis"

                checked: _root.action.direction === 90
                onClicked: function() {
                    _root.action.direction = 90
                }
            }

            RadioButton {
                Layout.fillWidth: true

                text: "Y Axis"

                checked: _root.action.direction === 0
                onClicked: function() {
                    _root.action.direction = 0
                }
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.horizontalStretchFactor: 1
            }

            Label {
                Layout.fillWidth: true

                text: "Minimum speed"
            }

            SpinBox {
                id: _min_speed_axis

                Layout.fillWidth: true

                value: _root.action.minSpeed
                from: limitLow
                to: _max_speed_axis.value
                editable: true

                onValueModified: function() {
                    _root.action.minSpeed = value
                }
            }

            Label {
                Layout.fillWidth: true

                text: "Maximum speed"
            }

            SpinBox {
                id: _max_speed_axis

                Layout.fillWidth: true

                value: _root.action.maxSpeed
                from: _min_speed_axis.value
                to: limitHigh
                editable: true

                onValueModified: function() {
                    _root.action.maxSpeed = value
                }
            }
        }

        // Motion configuration for hat inputs
        GridLayout {
            visible: _mode_motion.checked && inputBinding.behavior === "hat"

            columns: 4

            Label {
                Layout.fillWidth: true

                text: "Minimum speed"
            }

            SpinBox {
                id: _min_speed_hat

                Layout.fillWidth: true

                value: _root.action.minSpeed
                from: limitLow
                to: _max_speed_hat.value
                editable: true

                onValueModified: function() {
                    _root.action.minSpeed = value
                }
            }

            Label {
                Layout.fillWidth: true

                text: "Maximum speed"
            }

            SpinBox {
                id: _max_speed_hat

                Layout.fillWidth: true

                value: _root.action.maxSpeed
                from: _min_speed_hat.value
                to: limitHigh
                editable: true

                onValueModified: function() {
                    _root.action.maxSpeed = value
                }
            }

            Label {
                text: "Time to maximum speed"
            }

            FloatSpinBox {
                minValue: 0
                maxValue: 30
                value: _root.action.timeToMaxSpeed
                stepSize: 1.0
                decimals: 1

                onValueModified: (newValue) => {
                    _root.action.timeToMaxSpeed = newValue
                }
            }
        }
    }
}