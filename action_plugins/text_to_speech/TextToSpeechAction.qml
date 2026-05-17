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

            JGSpinBox {
                value: _root.action !== null ? _root.action.playbackVolume : 100
                from: 0
                to: 100

                onValueModified: () => {
                    if (_root.action !== null) {
                        _root.action.playbackVolume = value
                    }
                }
            }

            LayoutHorizontalSpacer {}

            Label {
                text: "Rate"
            }

            JGSpinBox {
                value: _root.action !== null ? _root.action.playbackRate : 0
                from: -10
                to: 10

                onValueModified: () => {
                    if (_root.action !== null) {
                        _root.action.playbackRate = value
                    }
                }
            }

            LayoutHorizontalSpacer {}

            Label {
                text: "Pitch"
            }

            JGSpinBox {
                value: _root.action !== null ? _root.action.playbackPitch : 0
                from: -10
                to: 10

                onValueModified: () => {
                    if (_root.action !== null) {
                        _root.action.playbackPitch = value
                    }
                }
            }
        }
    }
}
