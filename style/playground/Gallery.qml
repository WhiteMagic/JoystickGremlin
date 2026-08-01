// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only
//
// The Kobold style gallery: every standalone-testable type -- the 20 style
// templates plus the Kobold.Controls / Kobold.Composites leaves that need
// nothing but QtQuick + Foundation. Types needing device/app init
// (VJoySelector, LogicalDeviceSelector, InputCaptureButton, AxesStateCurrent,
// AxesStateSeries, ButtonState, HatView, InputBehavior) or the running app
// (ActionNode, InputButton, every other Kobold.Views type) are out of scope
// -- verified in the live app instead, not a gallery gap to close.

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kobold.Foundation
import Kobold.Controls
import Kobold.Composites

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

        // -- DoubleSpinBox -------------------------------------------------
        Section {
            title: "DoubleSpinBox"

            ColumnLayout {
                spacing: Metrics.gapS
                DoubleSpinBox { from: 0; to: 100; stepSize: 0.1; decimals: 2; value: 42.5 }
                Caption { text: "rest" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                DoubleSpinBox {
                    from: 0; to: 100; stepSize: 0.1; decimals: 2; value: 42.5
                    enabled: false
                }
                Caption { text: "disabled" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                DoubleSpinBox { from: -1.0; to: 1.0; stepSize: 0.1; decimals: 3; value: 0.5 }
                Caption { text: "live -- click +/-, type a value, hover, tab" }
            }
        }

        // -- RangeSlider -------------------------------------------------
        Section {
            title: "RangeSlider"

            ColumnLayout {
                spacing: Metrics.gapS
                RangeSlider {
                    from: 0; to: 100
                    first.value: 25; second.value: 75
                }
                Caption { text: "rest -- accent-filled span between handles" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                RangeSlider {
                    from: 0; to: 100
                    first.value: 25; second.value: 75
                    enabled: false
                }
                Caption { text: "disabled" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                RangeSlider { from: 0; to: 100; first.value: 10; second.value: 90 }
                Caption { text: "live -- drag either handle" }
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

        // -- MenuBar / MenuBarItem ---------------------------------------
        Section {
            title: "MenuBar / MenuBarItem"

            ColumnLayout {
                spacing: Metrics.gapS

                MenuBar {
                    Layout.preferredWidth: Metrics.ctrlH * 8

                    Menu {
                        title: "File"
                        MenuItem { text: "Open" }
                        MenuItem { text: "Save" }
                    }
                    Menu {
                        title: "Edit"
                        MenuItem { text: "Undo" }
                    }
                    Menu {
                        title: "Disabled"
                        enabled: false
                        MenuItem { text: "n/a" }
                    }
                }
                Caption { text: "live -- hover/open each menu; bgHover only, never accent-filled" }
            }
        }

        // -- ToolBar -------------------------------------------------
        Section {
            title: "ToolBar"

            ColumnLayout {
                spacing: Metrics.gapS

                ToolBar {
                    Layout.preferredWidth: Metrics.ctrlH * 8

                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: Metrics.gapM
                        spacing: Metrics.gapM

                        ToolButton { icon.name: "check" }
                        ToolButton { text: "Action" }
                    }
                }
                Caption { text: "bgAlt fill, ties into the shell frame" }
            }
        }

        // -- SplitView -----------------------------------------------
        Section {
            title: "SplitView"

            ColumnLayout {
                spacing: Metrics.gapS

                SplitView {
                    Layout.preferredWidth: Metrics.ctrlH * 10
                    Layout.preferredHeight: Metrics.ctrlH * 4

                    Rectangle {
                        SplitView.preferredWidth: Metrics.ctrlH * 4
                        color: Theme.bgAlt
                        Text { anchors.centerIn: parent; text: "Left"; color: Theme.fg }
                    }
                    Rectangle {
                        color: Theme.bg
                        Text { anchors.centerIn: parent; text: "Right"; color: Theme.fg }
                    }
                }
                Caption { text: "live -- drag the 1px handle; no grip decoration, no shadow" }
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

        // -- NumericRangeSlider (Kobold.Controls) ------------------------
        Section {
            title: "NumericRangeSlider (Kobold.Controls)"

            ColumnLayout {
                spacing: Metrics.gapS

                NumericRangeSlider {
                    id: _rangeDemo
                    from: -1.0
                    to: 1.0
                    stepSize: 0.1
                    decimals: 3
                    firstValue: -0.5
                    secondValue: 0.5

                    onFirstValueEdited: (value) => { firstValue = value }
                    onSecondValueEdited: (value) => { secondValue = value }
                }
                Caption { text: "live -- drag the slider or edit either mono value field" }
            }
        }

        // -- HatDirectionToggle (Kobold.Controls) ------------------------
        Section {
            title: "HatDirectionToggle (Kobold.Controls)"

            ColumnLayout {
                spacing: Metrics.gapS

                HatDirectionToggle {
                    id: _hatDemo
                    north: true
                    east: true

                    onNorthEdited: (value) => { north = value }
                    onNorthEastEdited: (value) => { northEast = value }
                    onEastEdited: (value) => { east = value }
                    onSouthEastEdited: (value) => { southEast = value }
                    onSouthEdited: (value) => { south = value }
                    onSouthWestEdited: (value) => { southWest = value }
                    onWestEdited: (value) => { west = value }
                    onNorthWestEdited: (value) => { northWest = value }
                }
                Caption { text: "live -- toggle any direction; accent-shaded when selected" }
            }
        }

        // -- AddActionMenuButton (Kobold.Controls) ------------------------
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

        // -- Divider (Kobold.Controls) ------------------------------------
        Section {
            title: "Divider (Kobold.Controls)"

            ColumnLayout {
                spacing: Metrics.gapM
                Layout.preferredWidth: Metrics.ctrlH * 8

                Label { text: "Row above" }
                Divider { Layout.fillWidth: true }
                Label { text: "Row below" }
                Caption { text: "fixed Theme.line hairline -- no color property, R4-safe by construction" }
            }
        }

        // -- ButtonStateSelector (Kobold.Controls) -------------------------
        Section {
            title: "ButtonStateSelector (Kobold.Controls)"

            ColumnLayout {
                spacing: Metrics.gapS

                ButtonStateSelector {
                    id: _buttonStateDemo
                    isPressed: true
                    onStateModified: (value) => { isPressed = value }
                }
                Caption { text: "live -- Press / Release" }
            }
        }

        // -- ScrollList (Kobold.Controls) -----------------------------------
        Section {
            title: "ScrollList (Kobold.Controls)"

            ScrollList {
                id: _scrollListDemo
                Layout.preferredWidth: Metrics.ctrlH * 8
                Layout.preferredHeight: Metrics.ctrlH * 5
                scrollbarAlwaysVisible: true
                model: 30
                delegate: Text {
                    text: "Row " + index
                    color: Theme.fg
                    font.family: FontType.sans
                    font.pixelSize: Metrics.textBody
                    height: Metrics.ctrlH
                }
            }
            Caption { text: "pixel wheel scrolling (wheelStep) -- shared by the left pane and plugin bodies (e.g. macro)" }
        }

        // -- TextInputDialog (Kobold.Controls) -----------------------------
        Section {
            title: "TextInputDialog (Kobold.Controls)"

            ColumnLayout {
                spacing: Metrics.gapS

                Button {
                    id: _textInputDialogButton
                    text: "Open dialog"
                    onClicked: _textInputDialogDemo.open()
                }
                Caption { text: "live -- open, type, accept/cancel" }

                TextInputDialog {
                    id: _textInputDialogDemo
                    text: "Rename me"
                }
            }
        }

        // -- BetterProgressBar (Kobold.Controls) ----------------------------
        Section {
            title: "BetterProgressBar (Kobold.Controls)"

            ColumnLayout {
                spacing: Metrics.gapS
                Layout.preferredWidth: Metrics.ctrlH * 8

                BetterProgressBar { Layout.fillWidth: true; value: 0.3 }
                Caption { text: "30%" }
            }
            ColumnLayout {
                spacing: Metrics.gapS
                Layout.preferredWidth: Metrics.ctrlH * 8

                BetterProgressBar { Layout.fillWidth: true; value: 0.75 }
                Caption { text: "75%" }
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
                    color: Theme.accent
                }
                Caption {
                    text: "2px insertion line in Theme.accent, shown at the row-edge band "
                        + "the pointer is over while dragging -- RowDropBand"
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

        // -- Not demoed here -------------------------------------------------------------
        Section {
            title: "Not demoed here"

            Caption {
                text: "InputCaptureButton, LogicalDeviceSelector, VJoySelector, "
                    + "AxesStateCurrent, AxesStateSeries, ButtonState, HatView, InputBehavior "
                    + "wrap Python models that need a running EventListener / connected "
                    + "device / loaded profile (InputListenerModel, LogicalDeviceSelectorModel, "
                    + "DeviceAxisState, InputItemBindingModel, ...). ActionNode and InputButton "
                    + "need the app's `backend`/`signal` context objects and a real action tree. "
                    + "All verified in the live app instead."
            }
        }

        Item { Layout.preferredHeight: Metrics.gapL }
    }
}
