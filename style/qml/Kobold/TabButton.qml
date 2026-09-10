// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.TabButton {
    id: control

    implicitHeight: Metrics.tabStrip
    implicitWidth: contentItem.implicitWidth + leftPadding + rightPadding
    leftPadding: Metrics.gapM
    rightPadding: Metrics.gapM

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody
    font.weight: FontType.regular

    contentItem: Text {
        text: control.text
        font: control.font
        color: control.enabled ? Theme.fg : Theme.fgDisabled
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    // Active = 2px accent underline + bgSelected (SPEC §10). Never accent-filled.
    background: Rectangle {
        color: control.checked ? Theme.bgSelected : control.hovered ? Theme.bgHover : Theme.bgAlt

        Rectangle {
            visible: control.checked
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: Metrics.accentMark
            color: Theme.accent
        }
    }
}
