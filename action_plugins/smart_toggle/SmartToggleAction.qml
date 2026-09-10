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

    required property SmartToggleModel action

    spacing: Metrics.gapM

    RowLayout {
        spacing: Metrics.gapM

        Label {
            text: "Toggle delay (sec)"
        }

        DoubleSpinBox {
            from: 0
            to: 100
            stepSize: 0.05
            decimals: Metrics.defaultDecimalPlaces
            value: root.action.delay

            onValueModified: { root.action.delay = value }
        }
    }

    SlotHeader {
        Layout.fillWidth: true

        label: "Actions"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "children") }
    }

    ActionList {
        Layout.fillWidth: true

        containerOwner: root.action
        containerName: "children"
    }
}
