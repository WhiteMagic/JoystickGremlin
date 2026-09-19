// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls

import Kobold.Foundation

// Menu to add actions implemented as a button that opens a drop down menu with valid
// choices. Upon selecting a choice the selection is added.
ToolButton {
    id: control

    property string variant: "ghost"
    property var model: []
    property color menuColor: Theme.bgAlt
    property color fillColor: Theme.bgAlt

    // When true the drop down menu's width matches that of the menu button.
    property bool menuMatchesWidth: false

    // Controls the direction in which the menu opens.
    property bool menuOpensUpward: false

    signal actionRequested(string name)

    readonly property bool bordered: control.variant === "bordered"
    readonly property bool ghostActive: !bordered && (control.hovered || control.down)
    readonly property string fgRole: bordered || ghostActive ? "fg" : "fgMuted"

    text: "Add action"
    implicitHeight: Metrics.controlHeight
    implicitWidth: Math.max(
        leftPadding + contentItem.implicitWidth + Metrics.gapM + indicator.width + rightPadding,
        _maxItemWidth)

    leftPadding: Metrics.gapS
    rightPadding: Metrics.gapS

    // Derive the maximum width of menu items.
    readonly property real _maxItemWidth: {
        let max = 0
        for (let i = 0; i < _menu.count; i++) {
            const item = _menu.itemAt(i)
            if (item) {
                max = Math.max(max, item.implicitWidth)
            }
        }
        return max
    }

    contentItem: Text {
        text: control.text
        color: control.fgRole === "fg" ? Theme.fg : Theme.fgMuted
        font.family: FontType.sans
        font.pixelSize: control.bordered ? Metrics.textBody : Metrics.textDetail
        verticalAlignment: Text.AlignVCenter
        leftPadding: Metrics.gapS
    }

    indicator: AppIcon {
        x: control.width - width - control.rightPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        name: "chevron-down"
        role: control.fgRole
    }

    // Handles the visual appearance of the button for the two different styles:
    // - ghost: no styling at rest, hover fill and edge on hover.
    // - bordered: an ordinary button fill with border.
    background: Rectangle {
        radius: control.bordered ? Metrics.radius : 0
        color: control.down    ? Theme.bgSelected
             : control.hovered ? Theme.bgHover
             : control.bordered ? control.fillColor
             :                    "transparent"
        border.width: Metrics.hairline
        border.color: control.bordered ? Theme.line
            : (control.ghostActive ? Theme.line : "transparent")
    }

    onClicked: { _menu.open() }

    Menu {
        id: _menu

        x: 0
        y: control.menuOpensUpward ? -_menu.height : control.height
        // Menu width matches the button's width by default.
        width: control.menuMatchesWidth ? control.width : control.implicitWidth
        fillColor: control.menuColor

        Repeater {
            model: control.model

            MenuItem {
                required property string modelData
                text: modelData
                onTriggered: { control.actionRequested(modelData) }
            }
        }
    }
}
