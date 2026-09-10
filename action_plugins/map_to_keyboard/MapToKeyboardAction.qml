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

    required property MapToKeyboardModel action

    RowLayout {
        spacing: Metrics.gapM

        Label {
            text: "Key combination"
        }

        InputCaptureButton {
            Layout.fillWidth: true

            eventTypes: ["key"]
            multipleInputs: true
            text: root.action.keyCombination.length > 0
                    ? root.action.keyCombination : "Record keys"

            callback: (inputs) => { root.action.updateInputs(inputs) }
        }
    }
}
