// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls

import Gremlin.Style

TabButton {
    font.pixelSize: 14
    font.weight: 600

    contentItem: Text {
        text: parent.text
        font: parent.font
        // Active tab at full strength; inactive tabs muted but still legible.
        color: parent.checked ? Style.foreground : Style.medColor

        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
    }

    background: Rectangle {
        color: parent.checked ? Style.accent : Style.background
    }
}
