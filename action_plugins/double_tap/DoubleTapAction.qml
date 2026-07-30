// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Controls
import Kobold.Foundation


// Body only -- no chevron, header, name field, guide or indent, those are the core's.
ColumnLayout {
    id: root

    required property DoubleTapModel action

    spacing: Metrics.gapM

    RowLayout {
        spacing: Metrics.gapM

        Text {
            text: "Double-tap threshold (sec)"
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

    // Single-tap sequence.
    SlotHeader {
        Layout.fillWidth: true

        label: "Single tap"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "single") }
    }

    Repeater {
        model: root.action.getActions("single")

        delegate: ActionNode {
            required property var modelData
            required property int index

            Layout.fillWidth: true

            action: modelData
            previousSibling: index > 0 ? root.action.getActions("single")[index - 1] : null
        }
    }

    // Double-tap sequence.
    SlotHeader {
        Layout.fillWidth: true

        label: "Double tap"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "double") }
    }

    Repeater {
        model: root.action.getActions("double")

        delegate: ActionNode {
            required property var modelData
            required property int index

            Layout.fillWidth: true

            action: modelData
            previousSibling: index > 0 ? root.action.getActions("double")[index - 1] : null
        }
    }
}
