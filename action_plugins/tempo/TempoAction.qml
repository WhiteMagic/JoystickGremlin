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

    required property TempoModel action

    spacing: Metrics.gapM

    RowLayout {
        spacing: Metrics.gapM

        Label {
            text: "Long-press threshold (sec)"
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
            text: "Press"
            checked: root.action.activateOn === "press"

            onToggled: { root.action.activateOn = "press" }
        }
        RadioButton {
            text: "Release"
            checked: root.action.activateOn === "release"

            onToggled: { root.action.activateOn = "release" }
        }
    }

    // +--------------------------------------------------------------------------------
    // | Long-press sequence.
    // +--------------------------------------------------------------------------------
    SlotHeader {
        Layout.fillWidth: true

        label: "Short press"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "short") }
    }

    ActionList {
        Layout.fillWidth: true

        containerOwner: root.action
        containerName: "short"
    }

    // +--------------------------------------------------------------------------------
    // | Long-press sequence.
    // +--------------------------------------------------------------------------------
    SlotHeader {
        Layout.fillWidth: true

        label: "Long press"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "long") }
    }

    ActionList {
        Layout.fillWidth: true

        containerOwner: root.action
        containerName: "long"
    }
}
