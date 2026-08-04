// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Layouts
import Kobold.Foundation

// SPEC §8, the crux of the tree grammar: an action's config, slot headers and child actions
// all sit one 16px step in from its header, sharing one 1px guide. A guide exists only to
// group child actions -- no children, no visible line -- but the 1px is still reserved so a
// config-only body aligns pixel-for-pixel with a guided sibling and the even grid holds.
// Test: cover the labels and you must still see where each slot starts.
RowLayout {
    id: root

    property bool hasChildren: false
    default property alias content: _content.data

    // ActionRow's name field is Metrics.controlHeight centered in the taller
    // Metrics.rowAction row, so its visible border sits this far inside the row's own
    // bottom edge -- subtracted from the content's top margin below so the *visible*
    // gap (box border to box border) matches Metrics.gapM, not the row-to-row gap plus
    // this inset on top of it.
    readonly property int _headerBoxInset: (Metrics.rowAction - Metrics.controlHeight) / 2

    spacing: 0

    Rectangle {
        Layout.preferredWidth: Metrics.hairline
        Layout.fillHeight: true
        color: root.hasChildren ? Theme.line : "transparent"
    }

    Item {
        Layout.preferredWidth: Metrics.indent - Metrics.hairline
    }

    ColumnLayout {
        id: _content

        Layout.fillWidth: true
        // The guide itself stays flush against the header above (fillHeight on the
        // guide Rectangle) -- only the content is inset, so the header-to-first-row
        // gap matches the row-to-row gap used inside the content (Metrics.gapM),
        // without floating the guide's own top away from the header's icon.
        Layout.topMargin: Metrics.gapM - root._headerBoxInset
        spacing: Metrics.gapM
    }
}
