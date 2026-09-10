// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T

import Kobold.Foundation

T.Button {
    id: control

    // Icon shade, as an AppIcon role. Bound so a theme change rides the binding graph.
    property string iconRole: enabled ? "fg" : "fgDisabled"

    // An icon without a label gets a square, like ToolButton, rather than the
    // two-height minimum a text label needs.
    readonly property bool iconOnly: icon.name !== "" && text === ""

    implicitHeight: Metrics.controlHeight
    implicitWidth: iconOnly ? Metrics.controlHeight
        : Math.max(Metrics.controlHeight * 2, contentItem.implicitWidth + Metrics.gapM * 2)
    padding: Metrics.gapM

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody

    contentItem: Item {
        // Computed rather than taken from the Row, whose width depends on the icon
        // having loaded -- an unloaded Image measures zero and the label would jump.
        implicitWidth: _icon.visible
            ? (_label.visible ? Metrics.icon + Metrics.gapM + _label.implicitWidth
                              : Metrics.icon)
            : _label.implicitWidth
        implicitHeight: Metrics.controlHeight

        // Centred as a group, so a stretched button keeps its content in the middle.
        Row {
            anchors.centerIn: parent
            spacing: _icon.visible && _label.visible ? Metrics.gapM : 0

            AppIcon {
                id: _icon
                anchors.verticalCenter: parent.verticalCenter
                visible: control.icon.name !== ""
                name: control.icon.name
                role: control.iconRole
                size: Metrics.icon
            }

            Text {
                id: _label
                anchors.verticalCenter: parent.verticalCenter
                visible: control.text !== ""
                text: control.text
                color: control.enabled ? Theme.fg : Theme.fgDisabled
                font: control.font
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    background: Rectangle {
        radius: Metrics.radius
        color: !control.enabled ? Theme.bgAlt
             : control.down     ? Theme.bgSelected
             : control.hovered  ? Theme.bgHover
             :                    Theme.bgAlt
        border.width: Metrics.hairline
        border.color: Theme.line

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
