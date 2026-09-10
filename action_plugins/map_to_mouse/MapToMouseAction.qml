// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Controls
import Kobold.Foundation


ColumnLayout {
    id: root

    required property MapToMouseModel action

    property int limitLow: 0
    property int limitHigh: 100000

    spacing: Metrics.gapM

    RowLayout {
        spacing: Metrics.gapM

        Label {
            text: "Mode"
        }

        RadioButton {
            id: _modeButton

            text: "Button"
            visible: root.action.actionBehavior === "button"
            checked: root.action.mode === "Button"

            onToggled: { root.action.mode = "Button" }
        }
        RadioButton {
            id: _modeMotion

            text: "Motion"
            checked: root.action.mode === "Motion"

            onToggled: { root.action.mode = "Motion" }
        }
    }

    // Button configuration.
    RowLayout {
        visible: _modeButton.checked
        spacing: Metrics.gapM

        Label {
            text: "Mouse button"
        }

        InputCaptureButton {
            Layout.fillWidth: true

            eventTypes: ["mouse"]
            multipleInputs: false
            text: root.action.button

            callback: (inputs) => { root.action.updateInputs(inputs) }
        }
    }

    // Motion configuration for button-like inputs.
    ColumnLayout {
        visible: _modeMotion.checked && root.action.actionBehavior === "button"
        spacing: Metrics.gapS

        RowLayout {
            spacing: Metrics.gapM

            Label {
                text: "Minimum speed"
            }

            SpinBox {
                id: _minSpeedButton

                from: root.limitLow
                to: _maxSpeedButton.value
                value: root.action.minSpeed

                onValueModified: { root.action.minSpeed = value }
            }

            Label {
                text: "Maximum speed"
            }

            SpinBox {
                id: _maxSpeedButton

                from: _minSpeedButton.value
                to: root.limitHigh
                value: root.action.maxSpeed

                onValueModified: { root.action.maxSpeed = value }
            }
        }

        RowLayout {
            spacing: Metrics.gapM

            Label {
                text: "Time to maximum speed"
            }

            DoubleSpinBox {
                from: 0
                to: 60
                stepSize: 1.0
                decimals: Metrics.defaultDecimalPlaces
                value: root.action.timeToMaxSpeed

                onValueModified: { root.action.timeToMaxSpeed = value }
            }

            Label {
                text: "Direction"
            }

            SpinBox {
                from: 0
                to: 360
                stepSize: 15
                value: root.action.direction

                onValueModified: { root.action.direction = value }
            }
        }
    }

    // Motion configuration for axis inputs.
    ColumnLayout {
        visible: _modeMotion.checked && root.action.actionBehavior === "axis"
        spacing: Metrics.gapS

        RowLayout {
            spacing: Metrics.gapM

            Label {
                text: "Control motion of"
            }

            RadioButton {
                text: "X axis"
                checked: root.action.direction === 90

                onToggled: { root.action.direction = 90 }
            }
            RadioButton {
                text: "Y axis"
                checked: root.action.direction === 0

                onToggled: { root.action.direction = 0 }
            }
        }

        RowLayout {
            spacing: Metrics.gapM

            Label {
                text: "Minimum speed"
            }

            SpinBox {
                id: _minSpeedAxis

                from: root.limitLow
                to: _maxSpeedAxis.value
                value: root.action.minSpeed

                onValueModified: { root.action.minSpeed = value }
            }

            Label {
                text: "Maximum speed"
            }

            SpinBox {
                id: _maxSpeedAxis

                from: _minSpeedAxis.value
                to: root.limitHigh
                value: root.action.maxSpeed

                onValueModified: { root.action.maxSpeed = value }
            }
        }
    }

    // Motion configuration for hat inputs.
    ColumnLayout {
        visible: _modeMotion.checked && root.action.actionBehavior === "hat"
        spacing: Metrics.gapS

        RowLayout {
            spacing: Metrics.gapM

            Label {
                text: "Minimum speed"
            }

            SpinBox {
                id: _minSpeedHat

                from: root.limitLow
                to: _maxSpeedHat.value
                value: root.action.minSpeed

                onValueModified: { root.action.minSpeed = value }
            }

            Label {
                text: "Maximum speed"
            }

            SpinBox {
                id: _maxSpeedHat

                from: _minSpeedHat.value
                to: root.limitHigh
                value: root.action.maxSpeed

                onValueModified: { root.action.maxSpeed = value }
            }
        }

        RowLayout {
            spacing: Metrics.gapM

            Label {
                text: "Time to maximum speed"
            }

            DoubleSpinBox {
                from: 0
                to: 30
                stepSize: 1.0
                decimals: Metrics.defaultDecimalPlaces
                value: root.action.timeToMaxSpeed

                onValueModified: { root.action.timeToMaxSpeed = value }
            }
        }
    }
}
