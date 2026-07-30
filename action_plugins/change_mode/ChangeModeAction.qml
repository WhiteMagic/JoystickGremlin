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

    required property ChangeModeModel action

    spacing: Metrics.gapM

    RowLayout {
        spacing: Metrics.gapM

        ComboBox {
            id: _changeType

            Layout.alignment: Qt.AlignTop

            model: ["Switch", "Previous", "Unwind", "Cycle", "Temporary"]

            Component.onCompleted: {
                currentIndex = find(root.action.changeType)
            }

            onActivated: { root.action.changeType = currentValue }
        }

        // Switch to a specific mode.
        RowLayout {
            visible: _changeType.currentValue === "Switch"
            spacing: Metrics.gapM

            Text {
                text: "Switch to mode"
                color: Theme.fg
                font.family: FontType.sans
                font.pixelSize: Metrics.textBody
            }

            ComboBox {
                id: _switchCombo

                Layout.preferredWidth: 200

                model: ModeListModel {}
                textRole: "name"
                valueRole: "name"

                Component.onCompleted: {
                    currentIndex = find(root.action.targetModes[0])
                }

                onActivated: {
                    root.action.setTargetMode(currentValue, 0)
                }

                Connections {
                    target: _changeType
                    function onActivated() {
                        if (_switchCombo.visible) {
                            _switchCombo.currentIndex = _switchCombo.find(
                                root.action.targetModes[0]
                            )
                        }
                    }
                }
            }
        }

        // Return to the previously active mode.
        RowLayout {
            visible: _changeType.currentValue === "Previous"

            Text {
                text: "Change to the previously active mode"
                color: Theme.fg
                font.family: FontType.sans
                font.pixelSize: Metrics.textBody
            }
        }

        // Unwind one mode from the stack.
        RowLayout {
            visible: _changeType.currentValue === "Unwind"

            Text {
                text: "Unwind one mode in the stack"
                color: Theme.fg
                font.family: FontType.sans
                font.pixelSize: Metrics.textBody
            }
        }

        // Cycle through a set of modes.
        RowLayout {
            visible: _changeType.currentValue === "Cycle"
            spacing: Metrics.gapM

            Text {
                Layout.alignment: Qt.AlignTop

                text: "Cycle through these modes"
                color: Theme.fg
                font.family: FontType.sans
                font.pixelSize: Metrics.textBody
            }

            ColumnLayout {
                spacing: Metrics.gapS

                Repeater {
                    model: root.action.targetModes

                    delegate: RowLayout {
                        id: _cycleRow

                        required property int index

                        spacing: Metrics.gapM

                        ComboBox {
                            Layout.preferredWidth: 200

                            model: ModeListModel {}
                            textRole: "name"
                            valueRole: "name"

                            Component.onCompleted: {
                                currentIndex = find(root.action.targetModes[_cycleRow.index])
                            }

                            onActivated: {
                                root.action.setTargetMode(currentValue, _cycleRow.index)
                            }
                        }

                        ToolButton {
                            icon.name: "delete"

                            onClicked: { root.action.deleteTargetMode(_cycleRow.index) }
                        }
                    }
                }

                Button {
                    text: "Add mode"

                    onClicked: { root.action.addTargetMode() }
                }
            }
        }

        // Temporarily switch to a mode while the input is held.
        RowLayout {
            visible: _changeType.currentValue === "Temporary"
            spacing: Metrics.gapM

            Text {
                text: "Temporarily switch to mode"
                color: Theme.fg
                font.family: FontType.sans
                font.pixelSize: Metrics.textBody
            }

            ComboBox {
                id: _temporaryCombo

                Layout.preferredWidth: 200

                model: ModeListModel {}
                textRole: "name"
                valueRole: "name"

                Component.onCompleted: {
                    currentIndex = find(root.action.targetModes[0])
                }

                onActivated: {
                    root.action.setTargetMode(currentValue, 0)
                }

                Connections {
                    target: _changeType
                    function onActivated() {
                        if (_temporaryCombo.visible) {
                            _temporaryCombo.currentIndex = _temporaryCombo.find(
                                root.action.targetModes[0]
                            )
                        }
                    }
                }
            }
        }
    }
}
