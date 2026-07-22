// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.ToolButton {
    id: control

    implicitHeight: Metrics.ctrlH
    implicitWidth: Math.max(Metrics.ctrlH, contentItem.implicitWidth + Metrics.gapM * 2)
    padding: Metrics.gapM

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody

    contentItem: Item {
        // Metrics.icon, not _icon.implicitWidth -- Image.implicitWidth follows
        // the loaded source's natural size (0 if it failed to load), not the
        // deliberate fixed size AppIcon renders at.
        implicitWidth: _icon.visible ? Metrics.icon : _label.implicitWidth
        implicitHeight: Metrics.ctrlH

        AppIcon {
            id: _icon
            anchors.centerIn: parent
            visible: control.icon.name !== ""
            name: control.icon.name
            role: control.enabled ? "fg" : "fgDisabled"
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
