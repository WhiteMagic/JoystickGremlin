// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only
//
// Playground "Internal" tab: app-only components (Kobold.Internal) that
// plugins never import. Driven by synthetic sample data -- no live
// profile needed to check row layout/overflow across themes and zooms.

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kobold.Foundation
import Kobold.Controls
import Kobold.Internal

ScrollView {
    id: root

    clip: true

    ColumnLayout {
        x: Metrics.gapL
        y: Metrics.gapL
        width: root.width - Metrics.gapL * 2
        spacing: Metrics.gapL * 2

        // -- InputButton ---------------------------------------------------
        Section {
            title: "InputButton -- empty / chips / overflow / selection / count"

            ColumnLayout {
                spacing: Metrics.gapS

                Repeater {
                    model: [
                        {
                            name: "Button 3 - Unused Button", description: "",
                            actionSequenceCount: 0, actionSequenceDisplayMode: "Chips",
                            actionLabels: []
                        },
                        {
                            name: "Axis 1 - Throttle", description: "Boost / Cruise",
                            actionSequenceCount: 4, actionSequenceDisplayMode: "Chips",
                            actionLabels: ["Tempo", "Chain", "Condition", "Response Curve"]
                        },
                        {
                            name: "Hat 1 - POV Hat", description: "",
                            actionSequenceCount: 8, actionSequenceDisplayMode: "Chips",
                            actionLabels: [
                                "Tempo", "Chain", "Condition", "Response Curve",
                                "Map to vJoy", "Merge Axis", "Macro", "Pulse"
                            ]
                        },
                        {
                            name: "Button 7 - Fire", description: "Primary Fire",
                            actionSequenceCount: 1, actionSequenceDisplayMode: "Chips",
                            actionLabels: ["Press"]
                        },
                        {
                            name: "Button 8 - Alt Fire", description: "",
                            actionSequenceCount: 2, actionSequenceDisplayMode: "Count",
                            actionLabels: ["Press", "Release"]
                        }
                    ]
                    delegate: InputButton {
                        // InputButton declaring any `required property` switches
                        // this delegate to strict mode -- modelData is no
                        // longer ambiently injected either, so it must be
                        // re-declared here to receive it at all.
                        required property var modelData

                        Layout.preferredWidth: 400
                        selected: index === 3

                        // Plain JS-array delegates don't get per-property
                        // role binding the way a real QAbstractListModel
                        // does -- forward explicitly from modelData.
                        name: modelData.name
                        description: modelData.description
                        actionSequenceCount: modelData.actionSequenceCount
                        actionSequenceDisplayMode: modelData.actionSequenceDisplayMode
                        actionLabels: modelData.actionLabels
                    }
                }
                Caption {
                    text: "unbound row / 4-action axis (all fit) / 8-action hat (+n overflow) / "
                        + "selected row / count-mode row -- all @ 400px"
                }
            }
        }

        // -- InputButton with edit/delete (LogicalDevice / KeyboardInputList) --
        Section {
            title: "InputButton -- edit/delete buttons"

            ColumnLayout {
                spacing: Metrics.gapS

                InputButton {
                    Layout.preferredWidth: 400
                    index: 0
                    name: "Custom Input Name"
                    description: ""
                    actionSequenceCount: 1
                    actionSequenceDisplayMode: "Chips"
                    actionLabels: ["Press"]

                    editButton: ToolButton { icon.name: "edit"; padding: Metrics.gapS }
                    deleteButton: ToolButton { icon.name: "delete"; padding: Metrics.gapS }
                }
                Caption { text: "as used by LogicalDevice.qml / KeyboardInputList.qml" }
            }
        }

        // -- Action tree: recursive grammar (ActionRow / SlotHeader / TreeIndent) --------
        Section {
            title: "Action tree -- recursive grammar (SPEC §8 worked example)"

            ColumnLayout {
                Layout.preferredWidth: 460
                spacing: 0

                ActionRow {
                    Layout.fillWidth: true
                    iconPath: Qt.resolvedUrl("../../action_plugins/action-placeholder.svg")
                    name: "Condition"
                }
                TreeIndent {
                    Layout.fillWidth: true
                    hasChildren: true

                    SlotHeader {
                        Layout.fillWidth: true
                        label: "True"
                        actionNames: ["Chain", "Macro", "Response Curve"]
                    }
                    ActionRow {
                        Layout.fillWidth: true
                        iconPath: Qt.resolvedUrl("../../action_plugins/action-placeholder.svg")
                        name: "Landing / Lights"
                    }
                    TreeIndent {
                        // Leaf: config only, no children -- no guide, width still reserved.
                        Layout.fillWidth: true
                        hasChildren: false

                        Text {
                            text: "[vJoy Device 1 ▾] [Hat 3 ▾]"
                            color: Theme.fgMuted
                            font.family: FontType.sans
                            font.pixelSize: Metrics.textDetail
                        }
                    }
                    SlotHeader {
                        Layout.fillWidth: true
                        label: "False"
                        actionNames: ["Chain", "Macro", "Response Curve"]
                    }
                    ActionRow {
                        Layout.fillWidth: true
                        iconPath: Qt.resolvedUrl("../../action_plugins/action-placeholder.svg")
                        name: "Power management"
                    }
                    TreeIndent {
                        Layout.fillWidth: true
                        hasChildren: true

                        SlotHeader {
                            Layout.fillWidth: true
                            label: "North"
                            actionNames: ["Map to Keyboard"]
                        }
                        ActionRow {
                            Layout.fillWidth: true
                            iconPath: Qt.resolvedUrl("../../action_plugins/action-placeholder.svg")
                            name: "Map to Keyboard"
                            showTriggerMode: true
                            activateOnPress: true
                            activateOnRelease: true
                        }
                    }
                }
                Caption {
                    text: "cover the labels: the guides alone still mark True/Landing, "
                        + "False/Power → North/Map"
                }
            }

            ColumnLayout {
                Layout.preferredWidth: 300
                spacing: Metrics.gapS

                ActionRow {
                    Layout.fillWidth: true
                    iconPath: Qt.resolvedUrl("../../action_plugins/action-placeholder.svg")
                    name: "Invalid action"
                    hasError: true
                    errorHint: "vJoy device 1 is not connected."
                }
                Caption { text: "error state -- hover the icon for the hint tooltip" }

                ActionRow {
                    Layout.fillWidth: true
                    iconPath: Qt.resolvedUrl("../../action_plugins/action-placeholder.svg")
                    name: "hover me"
                }
                Caption {
                    text: "at rest the name field's border is transparent (reserved, "
                        + "invisible) -- hover it to see line+bgAlt appear; the row itself "
                        + "has no hover fill of its own"
                }
                Caption {
                    text: "Kobold.Controls.ActionNode (the live wiring of this row onto a "
                        + "real ActionModel) is not demoed here -- it needs a real action "
                        + "tree and the app's `backend`/`signal` context objects, so it's "
                        + "verified in the live app instead."
                }
            }
        }

        // -- Drag & drop insertion-line convention ---------------------------------------
        Section {
            title: "Drag & drop -- row-edge band insertion line"

            ColumnLayout {
                spacing: Metrics.gapS

                Rectangle {
                    Layout.preferredWidth: 300
                    Layout.preferredHeight: Metrics.insertionLine
                    color: Theme.line
                }
                Caption {
                    text: "2px insertion line in Theme.line (never accent), shown at the "
                        + "row-edge band the pointer is over while dragging -- RowDropBand"
                }
            }
        }

        // -- ActionStepTable: macro steps render as a table, not nested actions ---------
        Section {
            title: "ActionStepTable -- macro steps render as a table"

            ColumnLayout {
                Layout.preferredWidth: 420
                spacing: Metrics.gapS

                ActionStepTable {
                    Layout.fillWidth: true
                    columns: ["Type", "Input", "Duration"]
                    rows: [
                        ["Key press", "F8", "—"],
                        ["Pause", "—", "250 ms"],
                        ["Key release", "F8", "—"]
                    ]
                }
                Caption { text: "flat rows, 1px line separators -- never indented ActionRows" }
            }
        }

        // -- Plugin type icons: every shipped action_plugins/*/icon.svg -----------------
        Section {
            title: "Plugin type icons -- all shipped action_plugins/*/icon.svg"

            ColumnLayout {
                spacing: Metrics.gapS

                Flow {
                    Layout.fillWidth: true
                    spacing: Metrics.gapM

                    Repeater {
                        model: [
                            { dir: "axis_delta", name: "Axis Delta" },
                            { dir: "chain", name: "Chain" },
                            { dir: "change_mode", name: "Change Mode" },
                            { dir: "condition", name: "Condition" },
                            { dir: "description", name: "Description" },
                            { dir: "double_tap", name: "Double Tap" },
                            { dir: "dual_axis_deadzone", name: "Dual Axis Deadzone" },
                            { dir: "hat_buttons", name: "Hat as Buttons" },
                            { dir: "load_profile", name: "Load Profile" },
                            { dir: "macro", name: "Macro" },
                            { dir: "map_to_keyboard", name: "Map to Keyboard" },
                            { dir: "map_to_logical_device", name: "Map to Logical Device" },
                            { dir: "map_to_mouse", name: "Map to Mouse" },
                            { dir: "map_to_vjoy", name: "Map to vJoy" },
                            { dir: "merge_axis", name: "Merge Axis" },
                            { dir: "pause_resume", name: "Pause and Resume" },
                            { dir: "play_sound", name: "Play Sound" },
                            { dir: "reference", name: "Reference" },
                            { dir: "response_curve", name: "Response Curve" },
                            { dir: "run_command", name: "Run Command" },
                            { dir: "smart_toggle", name: "Smart Toggle" },
                            { dir: "split_axis", name: "Split Axis" },
                            { dir: "tempo", name: "Tempo" },
                            { dir: "text_to_speech", name: "Text to Speech" }
                        ]

                        delegate: RowLayout {
                            required property var modelData

                            spacing: Metrics.gapS

                            Image {
                                source: "image://action-icon/"
                                    + Qt.resolvedUrl("../../action_plugins/" + modelData.dir + "/icon.svg")
                                    + "?c=" + Theme.fg.toString().slice(-6) + "&px=" + Metrics.icon
                                sourceSize.width: Metrics.icon
                                sourceSize.height: Metrics.icon
                                width: Metrics.icon
                                height: Metrics.icon
                                fillMode: Image.PreserveAspectFit
                                smooth: true
                            }
                            Text {
                                text: modelData.name
                                color: Theme.fg
                                font.family: FontType.sans
                                font.pixelSize: Metrics.textDetail
                            }
                        }
                    }
                }
                Caption {
                    text: "every plugin-authored type icon, tinted to fg via the shared "
                        + "IconProvider pipeline (image://action-icon/...) -- check both themes"
                }
            }
        }

        Item { Layout.preferredHeight: Metrics.gapL }
    }
}
