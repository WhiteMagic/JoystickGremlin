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

    spacing: 0

    Rectangle {
        Layout.preferredWidth: Metrics.indentGuide
        Layout.fillHeight: true
        color: root.hasChildren ? Theme.line : "transparent"
    }

    Item {
        Layout.preferredWidth: Metrics.indent - Metrics.indentGuide
    }

    ColumnLayout {
        id: _content

        Layout.fillWidth: true
        spacing: 0
    }
}
