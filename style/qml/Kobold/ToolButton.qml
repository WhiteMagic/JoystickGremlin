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
    implicitWidth: control.icon.name !== "" ? control.controlSize
        : Math.max(control.controlSize, contentItem.implicitWidth + Metrics.gapM * 2)
    padding: Metrics.gapM

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody

    // Override for the engaged-toggle icon shade.
    property string iconRole: control.enabled ? "fg" : "fgDisabled"

    contentItem: Item {
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
