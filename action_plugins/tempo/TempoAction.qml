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

    required property TempoModel action

    spacing: Metrics.gapM

    RowLayout {
        spacing: Metrics.gapM

        Text {
            text: "Long-press threshold (sec)"
            color: Theme.fg
            font.family: FontType.sans
            font.pixelSize: Metrics.textBody
        }

        DoubleSpinBox {
            from: 0
            to: 100
            stepSize: 0.05
            decimals: 2
            value: root.action.threshold

            onValueModified: { root.action.threshold = value }
        }

        Item { Layout.fillWidth: true }

        Text {
            text: "Activate on"
            color: Theme.fg
            font.family: FontType.sans
            font.pixelSize: Metrics.textBody
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

    // Short-press sequence.
    SlotHeader {
        Layout.fillWidth: true

        label: "Short press"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "short") }
    }

    Repeater {
        model: root.action.getActions("short")

        delegate: ActionNode {
            required property var modelData
            required property int index

            Layout.fillWidth: true

            action: modelData
            previousSibling: index > 0 ? root.action.getActions("short")[index - 1] : null
        }
    }

    // Long-press sequence.
    SlotHeader {
        Layout.fillWidth: true

        label: "Long press"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "long") }
    }

    Repeater {
        model: root.action.getActions("long")

        delegate: ActionNode {
            required property var modelData
            required property int index

            Layout.fillWidth: true

            action: modelData
            previousSibling: index > 0 ? root.action.getActions("long")[index - 1] : null
        }
    }
}
