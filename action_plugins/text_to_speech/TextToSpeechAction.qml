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
            Label {
                text: "Text to speak"
            }

            ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: 80

                ScrollBar.vertical.interactive: true
                ScrollBar.horizontal.policy: ScrollBar.AlwaysOff

                TextArea {
                    wrapMode: TextArea.Wrap
                    placeholderText: "Enter text to speak"
                    text: _root.action !== null ? _root.action.text : ""
                    selectByMouse: true

                    onTextChanged: () => {
                        if (_root.action !== null) {
                            _root.action.text = text
                        }
                    }
                }
            }
        }

        RowLayout {
            CheckBox {
                text: "Interrupt current speech"

                checked: _root.action !== null ? _root.action.interruptRunning : false

                onToggled: () => {
                    if (_root.action !== null) {
                        _root.action.interruptRunning = checked
                    }
                }
            }
        }

        RowLayout {
            Label {
                text: "Volume"
            }

            FloatSpinBox {
                value: _root.action !== null ? _root.action.playbackVolume : 1.0
                minValue: 0.0
                maxValue: 1.0
                stepSize: 0.05

                onValueModified: (v) => {
                    if (_root.action !== null) {
                        _root.action.playbackVolume = v
                    }
                }
            }

            LayoutHorizontalSpacer {}

            Label {
                text: "Rate"
            }

            FloatSpinBox {
                value: _root.action !== null ? _root.action.playbackRate : 0.0
                minValue: -1.0
                maxValue: 1.0
                stepSize: 0.1

                onValueModified: (v) => {
                    if (_root.action !== null) {
                        _root.action.playbackRate = v
                    }
                }
            }

            LayoutHorizontalSpacer {}

            Label {
                text: "Pitch"
            }

            FloatSpinBox {
                value: _root.action !== null ? _root.action.playbackPitch : 0.0
                minValue: -1.0
                maxValue: 1.0
                stepSize: 0.1

                onValueModified: (v) => {
                    if (_root.action !== null) {
                        _root.action.playbackPitch = v
                    }
                }
            }
        }
    }
}
