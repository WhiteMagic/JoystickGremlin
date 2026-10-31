// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Controls
import Kobold.Foundation


ColumnLayout {
    id: root

    required property PauseResumeModel action

    RowLayout {
        spacing: Metrics.gapM

        RadioButton {
            objectName: "pauseRadio"

            text: "Pause"
            checked: root.action.operation === "Pause"

            onToggled: { root.action.operation = "Pause" }
        }
        RadioButton {
            objectName: "resumeRadio"

            text: "Resume"
            checked: root.action.operation === "Resume"

            onToggled: { root.action.operation = "Resume" }
        }
        RadioButton {
            objectName: "toggleRadio"

            text: "Toggle"
            checked: root.action.operation === "Toggle"

            onToggled: { root.action.operation = "Toggle" }
        }
    }
}
