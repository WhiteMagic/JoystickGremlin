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
                    iconName: "check"
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
                        iconName: "check"
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
                        iconName: "check"
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
                            iconName: "check"
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
                    iconName: "check"
                    name: "Invalid action"
                    hasError: true
                    errorHint: "vJoy device 1 is not connected."
                }
                Caption { text: "error state -- hover the icon for the hint tooltip" }

                ActionRow {
                    Layout.fillWidth: true
                    iconName: "check"
                    name: "hover me"
                }
                Caption {
                    text: "at rest the name field's border is transparent (reserved, "
                        + "invisible) -- hover it to see line+bgAlt appear; the row itself "
                        + "has no hover fill of its own"
                }
            }
        }

        // -- AddActionMenuButton: ghost (slot header) vs bordered (binding header) -------
        Section {
            title: "AddActionMenuButton -- ghost / bordered chrome"

            ColumnLayout {
                spacing: Metrics.gapS

                RowLayout {
                    spacing: Metrics.gapL

                    AddActionMenuButton {
                        variant: "ghost"
                        model: ["Condition", "Chain", "Macro", "Tempo"]
                    }
                    AddActionMenuButton {
                        variant: "bordered"
                        model: ["Condition", "Chain", "Macro", "Tempo"]
                    }
                }
                Caption {
                    text: "ghost: no chrome at rest, edge-only on hover, never filled / "
                        + "bordered: an ordinary button, always"
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

        Item { Layout.preferredHeight: Metrics.gapL }
    }
}
