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
//
// The guide sits at Metrics.indent / 2, not flush left -- that's where ActionRow's chevron
// (controlHeight-wide, icon centered) points, and the guide is that chevron's plumb line.
RowLayout {
    id: root

    property bool hasChildren: false
    default property alias content: _content.data

    spacing: 0

    Item {
        Layout.preferredWidth: Metrics.indent
        Layout.fillHeight: true

        Rectangle {
            width: Metrics.hairline
            height: parent.height
            anchors.horizontalCenter: parent.horizontalCenter
            color: root.hasChildren ? Theme.line : "transparent"
        }
    }

    ColumnLayout {
        id: _content

        Layout.fillWidth: true
        // The guide itself stays flush against the header above (fillHeight on the
        // guide Rectangle) -- only the content is inset, so the header-to-first-row
        // gap matches the row-to-row gap used inside the content (Metrics.gapM),
        // without floating the guide's own top away from the header's icon.
        Layout.topMargin: Metrics.gapM - Metrics.actionRowInset
        spacing: Metrics.gapM
    }
}
