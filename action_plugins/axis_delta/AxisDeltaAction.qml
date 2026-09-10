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

    required property AxisDeltaModel action

    spacing: Metrics.gapM

    RowLayout {
        spacing: Metrics.gapM

        Label {
            text: "Change threshold"
        }

        DoubleSpinBox {
            from: 0.0001
            to: 2.0
            stepSize: 0.05
            decimals: Metrics.preciseDecimalPlaces
            value: root.action.changeThreshold

            onValueModified: { root.action.changeThreshold = value }
        }
    }

    // +--------------------------------------------------------------------------------
    // | Positive change actions
    // +--------------------------------------------------------------------------------
    SlotHeader {
        Layout.fillWidth: true

        label: "Positive change"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "positive") }
    }

    ActionList {
        Layout.fillWidth: true

        containerOwner: root.action
        containerName: "positive"
    }

    // +--------------------------------------------------------------------------------
    // | Negative change actions
    // +--------------------------------------------------------------------------------
    SlotHeader {
        Layout.fillWidth: true

        label: "Negative change"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "negative") }
    }

    ActionList {
        Layout.fillWidth: true

        containerOwner: root.action
        containerName: "negative"
    }
}
