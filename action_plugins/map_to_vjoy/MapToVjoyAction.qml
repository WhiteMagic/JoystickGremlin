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

    required property MapToVjoyModel action

    RowLayout {
        spacing: Metrics.gapM

        VJoySelector {
            validTypes: [root.action.actionBehavior]

            onSelectionChanged: (vjoyId, inputType, inputId) => {
                root.action.vjoyDeviceId = vjoyId
                root.action.vjoyInputType = inputType
                root.action.vjoyInputId = inputId
            }

            Component.onCompleted: {
                initialize(
                    root.action.vjoyDeviceId,
                    root.action.actionBehavior,
                    root.action.vjoyInputId
                )
            }
        }

        // UI for a physical axis behaving as an axis.
        RowLayout {
            visible: root.action.vjoyInputType === "axis"
            spacing: Metrics.gapM

            RadioButton {
                text: "Absolute"
                checked: root.action.axisMode === "absolute"

                onToggled: { root.action.axisMode = "absolute" }
            }
            RadioButton {
                id: _relativeMode

                text: "Relative"
                checked: root.action.axisMode === "relative"

                onToggled: { root.action.axisMode = "relative" }
            }

            Label {
                text: "Scaling"
                visible: _relativeMode.checked
            }

            DoubleSpinBox {
                visible: _relativeMode.checked
                from: 0
                to: 100
                stepSize: 0.1
                decimals: Metrics.defaultDecimalPlaces
                value: root.action.axisScaling

                onValueModified: { root.action.axisScaling = value }
            }
        }

        // UI for a button input.
        CheckBox {
            visible: root.action.vjoyInputType === "button"
            text: "Invert activation"
            checked: root.action.buttonInverted

            onToggled: { root.action.buttonInverted = checked }
        }
    }
}
