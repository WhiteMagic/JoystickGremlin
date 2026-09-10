// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Composites
import Kobold.Foundation


ColumnLayout {
    id: root

    required property DoubleTapModel action

    spacing: Metrics.gapM

    RowLayout {
        spacing: Metrics.gapM

        Label {
            text: "Double-tap threshold (sec)"
        }

        DoubleSpinBox {
            from: 0
            to: 100
            stepSize: 0.05
            decimals: Metrics.defaultDecimalPlaces
            value: root.action.threshold

            onValueModified: { root.action.threshold = value }
        }

        Spacer {}

        Label {
            text: "Activate on"
        }

        RadioButton {
            text: "Exclusive"
            checked: root.action.activateOn === "exclusive"

            onToggled: { root.action.activateOn = "exclusive" }
        }
        RadioButton {
            text: "Combined"
            checked: root.action.activateOn === "combined"

            onToggled: { root.action.activateOn = "combined" }
        }
    }

    // +--------------------------------------------------------------------------------
    // | Single-tap sequence.
    // +--------------------------------------------------------------------------------
    SlotHeader {
        Layout.fillWidth: true

        label: "Single tap"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "single") }
    }

    ActionList {
        Layout.fillWidth: true

        containerOwner: root.action
        containerName: "single"
    }

    // +--------------------------------------------------------------------------------
    // | Double-tap sequence.
    // +--------------------------------------------------------------------------------
    SlotHeader {
        Layout.fillWidth: true

        label: "Double tap"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "double") }
    }

    ActionList {
        Layout.fillWidth: true

        containerOwner: root.action
        containerName: "double"
    }
}
