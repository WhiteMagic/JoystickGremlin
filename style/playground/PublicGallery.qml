// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only
//
// Playground "Public" tab: Foundation tokens + every implemented Kobold
// style control -- the surface a plugin author actually sees/uses.

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kobold.Foundation

ScrollView {
    id: root

    clip: true

    ColumnLayout {
        x: Metrics.gapL
        y: Metrics.gapL
        width: root.width - Metrics.gapL * 2
        spacing: Metrics.gapL * 2

        // -- Tokens --------------------------------------------------
        Section {
            title: "Tokens -- Theme colours"

            Repeater {
                model: [
                    "bg", "bgAlt", "bgHover", "bgSelected", "line",
                    "fg", "fgMuted", "fgDisabled", "accent", "error", "warning"
                ]
                delegate: ColumnLayout {
                    spacing: Metrics.gapS

                    Rectangle {
                        Layout.preferredWidth: Metrics.ctrlH * 2
                        Layout.preferredHeight: Metrics.ctrlH
                        color: Theme[modelData]
                        border.width: Metrics.hairline
                        border.color: Theme.line
                    }
                    Caption { text: modelData }
                }
            }
        }

        // -- Type ------------------------------------------------------
        Section {
            title: "Type -- Sans / Mono × 400 / 600 × 12 / 14"

            ColumnLayout {
                spacing: Metrics.gapS

                Repeater {
                    model: [
                        { family: FontType.sans, familyName: "Sans", weight: FontType.regular, weightName: "400", size: Metrics.textDetail, sizeName: "12" },
                        { family: FontType.sans, familyName: "Sans", weight: FontType.semiBold, weightName: "600", size: Metrics.textDetail, sizeName: "12" },
                        { family: FontType.sans, familyName: "Sans", weight: FontType.regular, weightName: "400", size: Metrics.textBody, sizeName: "14" },
                        { family: FontType.sans, familyName: "Sans", weight: FontType.semiBold, weightName: "600", size: Metrics.textBody, sizeName: "14" },
                        { family: FontType.mono, familyName: "Mono", weight: FontType.regular, weightName: "400", size: Metrics.textDetail, sizeName: "12" },
                        { family: FontType.mono, familyName: "Mono", weight: FontType.semiBold, weightName: "600", size: Metrics.textDetail, sizeName: "12" },
                        { family: FontType.mono, familyName: "Mono", weight: FontType.regular, weightName: "400", size: Metrics.textBody, sizeName: "14" },
                        { family: FontType.mono, familyName: "Mono", weight: FontType.semiBold, weightName: "600", size: Metrics.textBody, sizeName: "14" }
                    ]
                    delegate: Text {
                        text: modelData.familyName + " " + modelData.weightName + " " + modelData.sizeName + "px -- 0123456789"
                        color: Theme.fg
                        font.family: modelData.family
                        font.pixelSize: modelData.size
                        font.weight: modelData.weight
                    }
                }
            }
        }

        // -- Icons -----------------------------------------------------
        Section {
            title: "AppIcon -- recolours per role"

            Repeater {
                model: ["fg", "fgMuted", "fgDisabled", "accent", "error", "warning"]
                delegate: ColumnLayout {
                    spacing: Metrics.gapS

                    RowLayout {
                        spacing: Metrics.gapM
                        AppIcon { name: "check"; role: modelData }
                        AppIcon { name: "chevron-down"; role: modelData }
                    }
                    Caption { text: modelData }
                }
            }
        }

        // -- Button ------------------------------------------------------
        Section {
            title: "Button"

            ColumnLayout {
                spacing: Metrics.gapS
                Button { text: "Button" }
                Caption { text: "rest" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                Button { text: "Button"; down: true }
                Caption { text: "pressed" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                Button { text: "Button"; enabled: false }
                Caption { text: "disabled" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                Button { text: "Hover / Tab me" }
                Caption { text: "live -- hover/focus" }
            }
        }

        // -- ToolButton ----------------------------------------------
        Section {
            title: "ToolButton"

            ColumnLayout {
                spacing: Metrics.gapS
                ToolButton { text: "Tool" }
                Caption { text: "rest" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                ToolButton { text: "Tool"; down: true }
                Caption { text: "pressed" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                ToolButton { text: "Tool"; enabled: false }
                Caption { text: "disabled" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                ToolButton { text: "Hover / Tab" }
                Caption { text: "live -- hover/focus" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                ToolButton { icon.name: "check" }
                Caption { text: "icon-only" }
            }
        }

        // -- CheckBox ---------------------------------------------------
        Section {
            title: "CheckBox"

            ColumnLayout {
                spacing: Metrics.gapS
                CheckBox { text: "Unchecked" }
                Caption { text: "rest" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                CheckBox { text: "Checked"; checked: true }
                Caption { text: "checked" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                CheckBox { text: "Disabled"; checked: true; enabled: false }
                Caption { text: "disabled" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                CheckBox { text: "Hover / Tab me" }
                Caption { text: "live -- hover/focus" }
            }
        }

        // -- RadioButton --------------------------------------------
        Section {
            title: "RadioButton"

            ColumnLayout {
                spacing: Metrics.gapS
                RadioButton { text: "Option A" }
                Caption { text: "rest" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                RadioButton { text: "Option B"; checked: true }
                Caption { text: "checked" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                RadioButton { text: "Disabled"; enabled: false }
                Caption { text: "disabled" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                RadioButton { text: "Hover / Tab me" }
                Caption { text: "live -- hover/focus" }
            }
        }

        // -- TextField -------------------------------------------------
        Section {
            title: "TextField"

            ColumnLayout {
                spacing: Metrics.gapS
                TextField { placeholderText: "placeholder" }
                Caption { text: "rest" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                TextField { text: "Some text" }
                Caption { text: "filled" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                TextField { text: "Disabled"; enabled: false }
                Caption { text: "disabled" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                TextField { placeholderText: "Click / Tab me" }
                Caption { text: "live -- focus" }
            }
        }

        // -- SpinBox -----------------------------------------------------
        Section {
            title: "SpinBox"

            ColumnLayout {
                spacing: Metrics.gapS
                SpinBox { from: 0; to: 100; value: 42 }
                Caption { text: "rest" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                SpinBox { from: 0; to: 100; value: 42; enabled: false }
                Caption { text: "disabled" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                SpinBox { from: 0; to: 100; value: 7 }
                Caption { text: "live -- click +/-, hover, tab" }
            }
        }

        // -- ComboBox ---------------------------------------------------
        Section {
            title: "ComboBox"

            ColumnLayout {
                spacing: Metrics.gapS
                ComboBox { model: ["Alpha", "Beta", "Gamma"] }
                Caption { text: "rest" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                ComboBox { model: ["Alpha", "Beta", "Gamma"]; enabled: false }
                Caption { text: "disabled" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                ComboBox { model: ["Open me", "To see", "The popup"] }
                Caption { text: "live -- open the popup" }
            }
        }

        // -- Menu / MenuItem ---------------------------------------------
        Section {
            title: "Menu / MenuItem"

            ColumnLayout {
                spacing: Metrics.gapS

                Button {
                    id: _menuButton
                    text: "Open menu ▾"
                    onClicked: _exampleMenu.popup(_menuButton, 0, _menuButton.height)
                }
                Caption { text: "live -- plain / checkable / disabled items" }

                Menu {
                    id: _exampleMenu
                    MenuItem { text: "Plain item" }
                    MenuItem { text: "Checkable item"; checkable: true; checked: true }
                    MenuItem { text: "Disabled item"; enabled: false }
                }
            }
        }

        // -- ScrollBar / ListView -----------------------------------
        Section {
            title: "ScrollBar"

            ListView {
                id: _demoList
                Layout.preferredWidth: Metrics.ctrlH * 8
                Layout.preferredHeight: Metrics.ctrlH * 5
                clip: true
                model: 30
                delegate: Text {
                    text: "Row " + index
                    color: Theme.fg
                    font.family: FontType.sans
                    font.pixelSize: Metrics.textBody
                    height: Metrics.ctrlH
                }
                ScrollBar.vertical: ScrollBar { }

                // Disable mobile-style kinetic/overshoot scrolling.
                flickableDirection: Flickable.VerticalFlick
                boundsBehavior: Flickable.StopAtBounds
            }
        }

        // -- ToolTip -----------------------------------------------------
        Section {
            title: "ToolTip"

            ColumnLayout {
                spacing: Metrics.gapS

                Button {
                    text: "Hover me"
                    ToolTip.visible: hovered
                    ToolTip.text: "Kobold ToolTip"
                    ToolTip.delay: 200
                }
                Caption { text: "live -- hover to show" }
            }
        }

        // -- TabBar / TabButton --------------------------------------
        Section {
            title: "TabBar / TabButton"

            ColumnLayout {
                spacing: Metrics.gapS

                TabBar {
                    currentIndex: 0
                    TabButton { text: "Devices" }
                    TabButton { text: "Scripts" }
                    TabButton { text: "Settings" }
                }
                Caption { text: "first tab active; click to switch" }
            }
        }

        // -- Label -------------------------------------------------------
        Section {
            title: "Label"

            ColumnLayout {
                spacing: Metrics.gapS
                Label { text: "Enabled label" }
                Caption { text: "rest" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                Label { text: "Disabled label"; enabled: false }
                Caption { text: "disabled" }
            }
        }

        Item { Layout.preferredHeight: Metrics.gapL }
    }
}
