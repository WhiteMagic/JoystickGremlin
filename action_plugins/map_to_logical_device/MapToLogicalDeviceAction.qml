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

    required property MapToLogicalDeviceModel action

    RowLayout {
        spacing: Metrics.gapM

        LogicalDeviceSelector {
            // The ordering is important, swapping it will result in the
            // wrong item being displayed.
            validTypes: [root.action.actionBehavior]
            logicalInputType: root.action.actionBehavior
            logicalInputIdentifier: root.action.logicalInputIdentifier

            onLogicalInputIdentifierChanged: {
                root.action.logicalInputIdentifier = logicalInputIdentifier
            }
        }

        // UI for a physical axis behaving as an axis.
        RowLayout {
            visible: root.action.logicalInputType === "axis"
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
                stepSize: 0.05
                decimals: Metrics.defaultDecimalPlaces
                value: root.action.axisScaling

                onValueModified: { root.action.axisScaling = value }
            }
        }

        // UI for a button input.
        CheckBox {
            visible: root.action.logicalInputType === "button"
            text: "Invert activation"
            checked: root.action.buttonInverted

            onToggled: { root.action.buttonInverted = checked }
        }
    }
}
