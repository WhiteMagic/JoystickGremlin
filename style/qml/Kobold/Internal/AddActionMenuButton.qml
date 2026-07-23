// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import Kobold.Foundation

// SPEC §7: the action selector is a menu button, not a combo -- no value, no selection
// state, the label never changes ("Add action"). One click opens a menu of choices; picking
// one both selects and commits in the same act. Two chrome variants share this one behavior:
// "ghost" is the slot-header's chrome-on-hover-only trigger; "bordered" is the binding
// header's ordinary (unfilled) bordered button (SPEC §8: "chrome above the tree is chromed").
//
// Label in `contentItem`, caret as a separately positioned `indicator` -- the same split
// ComboBox.qml uses. A single RowLayout as contentItem does NOT get vertically centered by
// the control (it keeps its own top-left-packed natural size), which is what made an
// earlier version of this look crooked.
ToolButton {
    id: control

    property string variant: "ghost"
    property var model: []

    signal actionRequested(string name)

    readonly property bool bordered: control.variant === "bordered"
    readonly property bool ghostActive: !bordered && (control.hovered || control.down)
    readonly property string fgRole: bordered || ghostActive ? "fg" : "fgMuted"

    text: "Add action"
    implicitHeight: Metrics.ctrlH
    // Wide enough for its own label AND the widest menu entry -- the popup is pinned to
    // this same width (below), so it must never be narrower than what it needs to show
    // without eliding.
    implicitWidth: Math.max(
        leftPadding + contentItem.implicitWidth + Metrics.gapM + indicator.width + rightPadding,
        _maxItemWidth)

    leftPadding: Metrics.gapS
    rightPadding: Metrics.gapS

    // Read the width straight off the real, already-instantiated MenuItems (Repeater
    // delegates are created eagerly, not deferred until first open) rather than
    // re-estimating it with TextMetrics -- a second, independent measurement of the same
    // text can drift a few px from what MenuItem.qml's Text actually lays out, which is
    // exactly what caused the longest entry to still elide.
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
    }

    indicator: AppIcon {
        x: control.width - width - control.rightPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        name: "chevron-down"
        role: control.fgRole
    }

    // Ghost: no chrome at rest, an edge only on hover -- never a fill, never accent.
    // Bordered: an ordinary button fill + border, always.
    background: Rectangle {
        radius: control.bordered ? Metrics.radius : 0
        color: control.bordered ? Theme.bgAlt : "transparent"
        border.width: Metrics.hairline
        border.color: control.bordered ? Theme.line
            : (control.ghostActive ? Theme.line : "transparent")
    }

    onClicked: _menu.open()

    Menu {
        id: _menu

        x: 0
        y: control.height
        width: control.width

        Repeater {
            model: control.model

            MenuItem {
                required property string modelData
                text: modelData
                onTriggered: control.actionRequested(modelData)
            }
        }
    }
}
