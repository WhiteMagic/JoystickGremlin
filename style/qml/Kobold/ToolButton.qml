// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.ToolButton {
    id: control

    property int controlSize: Metrics.controlHeight
    property int iconSize: Metrics.icon

    implicitHeight: control.controlSize
    // Icon-only buttons are a square, one control size on a side -- not padded out to
    // whatever the text formula below would give them (icon 16 + gapM*2 = 32, wider than
    // the 24px default height). Text buttons keep the padded, content-driven width.
    implicitWidth: control.icon.name !== "" ? control.controlSize
        : Math.max(control.controlSize, contentItem.implicitWidth + Metrics.gapM * 2)
    padding: Metrics.gapM

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody

    // Override for the engaged-toggle icon shade (SPEC/architecture §2.5) -- the only
    // sanctioned non-selection/focus use of accent on an icon.
    property string iconRole: control.enabled ? "fg" : "fgDisabled"

    contentItem: Item {
        // control.iconSize, not _icon.implicitWidth -- Image.implicitWidth follows
        // the loaded source's natural size (0 if it failed to load), not the
        // deliberate fixed size AppIcon renders at.
        implicitWidth: _icon.visible ? control.iconSize : _label.implicitWidth
        implicitHeight: control.controlSize

        AppIcon {
            id: _icon
            anchors.centerIn: parent
            visible: control.icon.name !== ""
            name: control.icon.name
            role: control.iconRole
            size: control.iconSize
        }

        Text {
            id: _label
            anchors.centerIn: parent
            visible: !_icon.visible
            text: control.text
            color: control.enabled ? Theme.fg : Theme.fgDisabled
            font: control.font
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
        }
    }

    // Flat: no border at rest -- only the fill responds, per its toolbar-affordance role.
    background: Rectangle {
        radius: Metrics.radius
        color: !control.enabled  ? "transparent"
             : control.down     ? Theme.bgSelected
             : control.hovered  ? Theme.bgHover
             :                    "transparent"

        Rectangle {
            visible: control.visualFocus
            anchors.fill: parent
            anchors.margins: -2
            radius: parent.radius
            color: "transparent"
            border.width: 2
            border.color: Theme.accent
        }
    }
}
