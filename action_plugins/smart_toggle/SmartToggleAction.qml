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

    required property SmartToggleModel action

    spacing: Metrics.gapM

    RowLayout {
        spacing: Metrics.gapM

        Text {
            text: "Toggle delay (sec)"
            color: Theme.fg
            font.family: FontType.sans
            font.pixelSize: Metrics.textBody
        }

        DoubleSpinBox {
            from: 0
            to: 100
            stepSize: 0.05
            decimals: 2
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
