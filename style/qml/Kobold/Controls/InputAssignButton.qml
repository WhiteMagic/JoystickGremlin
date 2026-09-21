// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Kobold.Foundation

// Button showing the assigned input, clicking it assigns the currently selected input.
// Shares its look with the bordered InputCaptureButton.
ToolButton {
    id: control

    required property string valueLabel
    property bool isAssigned: true

    text: valueLabel

    // Setting icon.name would collapse the style's implicitWidth to a square, the icon
    // is part of the contentItem instead.
    implicitHeight: Metrics.controlHeight
    implicitWidth: leftPadding + implicitContentWidth + rightPadding

    leftPadding: Metrics.gapM
    rightPadding: Metrics.gapM
    topPadding: 0
    bottomPadding: 0

    contentItem: RowLayout {
        spacing: Metrics.gapM

        Spacer {}

        AppIcon {
            Layout.alignment: Qt.AlignVCenter
            name: "assign"
            role: control.enabled ? "fg" : "fgDisabled"
        }

        Label {
            id: _label

            Layout.fillHeight: true
            text: control.text
            color: control.isAssigned && control.enabled ? Theme.fg : Theme.fgDisabled
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter

            ToolTip {
                text: _label.text
                width: Metrics.tooltipWidth(contentWidth)
                visible: _hoverHandler.hovered
                delay: 500
            }

            HoverHandler {
                id: _hoverHandler
                acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            }
        }

        Spacer {}
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
