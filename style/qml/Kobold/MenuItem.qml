// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T

import Kobold.Foundation

T.MenuItem {
    id: control

    property int elide: Text.ElideRight

    implicitHeight: Metrics.rowAction
    implicitWidth: leftPadding + contentItem.implicitWidth + rightPadding
    // Menu's contentItem is a ListView, so without this every item falls back to its
    // own label width and the hover/selection.
    width: ListView.view ? ListView.view.width : implicitWidth
    spacing: Metrics.gapM

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody

    contentItem: Text {
        leftPadding: control.indicator && control.indicator.visible ? control.indicator.width + control.spacing : Metrics.gapM
        rightPadding: (control.arrow && control.arrow.visible ? control.arrow.width + control.spacing : 0) + Metrics.gapM
        text: control.text
        font: control.font
        color: control.enabled ? Theme.fg : Theme.fgDisabled
        verticalAlignment: Text.AlignVCenter
        elide: control.elide
    }

    indicator: Item {
        visible: control.checkable
        implicitWidth: Metrics.icon
        implicitHeight: Metrics.icon
        x: control.leftPadding
        y: control.topPadding + (control.availableHeight - height) / 2

        AppIcon {
            anchors.centerIn: parent
            name: "check"
            role: "accent"
            visible: control.checked
        }
    }

    arrow: AppIcon {
        visible: control.subMenu !== null
        x: control.width - width - control.rightPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        name: "chevron-down"
        role: control.enabled ? "fg" : "fgDisabled"
        rotation: -90
    }

    background: Rectangle {
        color: control.highlighted ? Theme.bgSelected : control.hovered ? Theme.bgHover : "transparent"
    }
}
