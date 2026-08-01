// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Composites
import Kobold.Foundation


// Body only -- no chevron, header, name field, guide or indent, those are the core's.
ColumnLayout {
    id: root

    required property AxisDeltaModel action

    property var _positiveActions: root.action.getActions("positive")
    property var _negativeActions: root.action.getActions("negative")

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
            decimals: 4
            value: root.action.changeThreshold

            onValueModified: { root.action.changeThreshold = value }
        }
    }

    // +-------------------------------------------------------------------
    // | Positive change actions
    // +-------------------------------------------------------------------
    SlotHeader {
        Layout.fillWidth: true

        label: "Positive change"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "positive") }
    }

    Repeater {
        model: root._positiveActions

        delegate: ActionNode {
            required property var modelData
            required property int index

            Layout.fillWidth: true

            action: modelData
            previousSibling: index > 0 ? root._positiveActions[index - 1] : null
        }
    }

    // +-------------------------------------------------------------------
    // | Negative change actions
    // +-------------------------------------------------------------------
    SlotHeader {
        Layout.fillWidth: true

        label: "Negative change"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "negative") }
    }

    Repeater {
        model: root._negativeActions

        delegate: ActionNode {
            required property var modelData
            required property int index

            Layout.fillWidth: true

            action: modelData
            previousSibling: index > 0 ? root._negativeActions[index - 1] : null
        }
    }
}
