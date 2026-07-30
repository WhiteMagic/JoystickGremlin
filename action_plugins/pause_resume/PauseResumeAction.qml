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

    required property PauseResumeModel action

    RowLayout {
        spacing: Metrics.gapM

        RadioButton {
            text: "Pause"
            checked: root.action.operation === "Pause"

            onToggled: { root.action.operation = "Pause" }
        }
        RadioButton {
            text: "Resume"
            checked: root.action.operation === "Resume"

            onToggled: { root.action.operation = "Resume" }
        }
        RadioButton {
            text: "Toggle"
            checked: root.action.operation === "Toggle"

            onToggled: { root.action.operation = "Toggle" }
        }
    }
}
