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

    required property SplitAxisModel action

    spacing: Metrics.gapM

    RowLayout {
        spacing: Metrics.gapM

        Label {
            text: "Split axis at"
        }

        DoubleSpinBox {
            from: -1.0
            to: 1.0
            stepSize: 0.05
            decimals: 4
            value: root.action.splitValue

            onValueModified: { root.action.splitValue = value }
        }
    }

    // +-------------------------------------------------------------------
    // | Lower split actions
    // +-------------------------------------------------------------------
    SlotHeader {
        Layout.fillWidth: true

        label: "Lower / left"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "lower") }
    }

    ActionList {
        Layout.fillWidth: true

        containerOwner: root.action
        containerName: "lower"
    }

    // +-------------------------------------------------------------------
    // | Upper split actions
    // +-------------------------------------------------------------------
    SlotHeader {
        Layout.fillWidth: true

        label: "Upper / right"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "upper") }
    }

    ActionList {
        Layout.fillWidth: true

        containerOwner: root.action
        containerName: "upper"
    }
}
