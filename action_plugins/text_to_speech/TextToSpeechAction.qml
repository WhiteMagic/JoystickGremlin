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

    required property TextToSpeechModel action

    spacing: Metrics.gapS

    TextField {
        Layout.fillWidth: true

        placeholderText: "Enter text to speak"
        text: root.action.text
        selectByMouse: true

        onTextChanged: { root.action.text = text }
    }

    RowLayout {
        spacing: Metrics.gapM

        ComboBox {
            readonly property var _labels: ["Interrupt", "Queue front", "Queue back"]
            readonly property var _values: ["interrupt", "queue-front", "queue-back"]

            model: _labels
            currentIndex: _values.indexOf(root.action.queueMode)

            onActivated: (index) => { root.action.queueMode = _values[index] }
        }

        Spacer {}

        Label {
            text: "Volume"
        }

        DoubleSpinBox {
            from: 0.0
            to: 1.0
            stepSize: 0.05
            decimals: 2
            value: root.action.playbackVolume

            onValueModified: { root.action.playbackVolume = value }
        }

        Spacer {}

        Label {
            text: "Rate"
        }

        DoubleSpinBox {
            from: -1.0
            to: 1.0
            stepSize: 0.1
            decimals: 2
            value: root.action.playbackRate

            onValueModified: { root.action.playbackRate = value }
        }

        Spacer {}

        Label {
            text: "Pitch"
        }

        DoubleSpinBox {
            from: -1.0
            to: 1.0
            stepSize: 0.1
            decimals: 2
            value: root.action.playbackPitch

            onValueModified: { root.action.playbackPitch = value }
        }
    }
}
