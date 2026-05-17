// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.ActionPlugins
import Gremlin.Profile
import "../../qml"


Item {
    id: _root

    property TextToSpeechModel action

    implicitHeight: _content.height

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        RowLayout {
            TextArea {
                Layout.fillWidth: true
                Layout.rightMargin: 10

                wrapMode: TextArea.Wrap
                placeholderText: "Enter text to speak"
                text: _root.action !== null ? _root.action.text : ""
                selectByMouse: true

                onTextChanged: () => { _root.action.text = text }
            }
        }

        RowLayout {
            CheckBox {
                text: "Interrupt current speech"

                checked: _root.action !== null ? _root.action.interruptRunning : false

                onToggled: () => { _root.action.interruptRunning = checked }
            }

            LayoutHorizontalSpacer {}

            Label {
                Layout.rightMargin: 5

                text: "Volume"
            }

            FloatSpinBox {
                value: _root.action !== null ? _root.action.playbackVolume : 1.0
                minValue: 0.0
                maxValue: 1.0
                stepSize: 0.05

                onValueModified: (val) => { _root.action.playbackVolume = val }
            }

            LayoutHorizontalSpacer {}

            Label {
                Layout.rightMargin: 5

                text: "Rate"
            }

            FloatSpinBox {
                value: _root.action !== null ? _root.action.playbackRate : 0.0
                minValue: -1.0
                maxValue: 1.0
                stepSize: 0.1

                onValueModified: (val) => { _root.action.playbackRate = val }
            }

            LayoutHorizontalSpacer {}

            Label {
                Layout.rightMargin: 5

                text: "Pitch"
            }

            FloatSpinBox {
                Layout.rightMargin: 10

                value: _root.action !== null ? _root.action.playbackPitch : 0.0
                minValue: -1.0
                maxValue: 1.0
                stepSize: 0.1

                onValueModified: (val) => { _root.action.playbackPitch = val }
            }
        }
    }
}
