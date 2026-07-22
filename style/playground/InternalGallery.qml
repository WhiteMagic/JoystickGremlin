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

        Item { Layout.preferredHeight: Metrics.gapL }
    }
}
