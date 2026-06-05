// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls

import Gremlin.Style

TabButton {
    id: _tab

    font.pixelSize: 14
    font.weight: 600

    // Explicit text colour so unselected tabs use the full theme foreground
    // instead of the dimmed default; selected tabs sit on the accent fill.
    contentItem: Text {
        text: _tab.text
        font: _tab.font
        // Selected: white on the accent fill. Hovered: the accent blue (same
        // as the scroll arrows). Otherwise: the normal theme foreground.
        color: _tab.checked
            ? "#ffffff"
            : (_tab.hovered ? Style.accent : Style.foreground)
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    background: Rectangle {
        color: _tab.checked ? Style.accent : Style.background
    }
}
