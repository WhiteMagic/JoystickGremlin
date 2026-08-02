// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import Kobold.Foundation

// SPEC §8 drag & drop feedback: drop targets are row-edge bands -- the upper/lower ~12px of
// a row, independent of the gap between rows, not "gap-dwellers". Feedback is always exactly
// a 2px insertion line in `accent`. No parting animation -- the drag ghost + insertion line
// is enough.
//
// Same shape as the legacy qml/DragDropArea.qml (validationCallback/dropCallback props) so a
// future call-site swap is drop-in, but restyled to the SPEC's edge-band + insertion-line
// convention instead of a fixed drop zone below the row.
DropArea {
    id: root

    property Item target: null
    property var validationCallback: null
    property var dropCallback: null
    // Spacing between rows in the enclosing list, e.g. ListView.spacing. Zero
    // (the default) keeps the line flush with the row edge, matching callers
    // whose rows have no gap between them.
    property real gap: 0

    readonly property real bandHeight: Metrics.gapL
    readonly property bool inTopBand: containsDrag && drag.y < bandHeight
    // Mime data is only reachable from the DragEvent handed to onEntered/onDropped, not
    // from any DropArea property -- so validity has to be tracked as mutable state
    // updated from those handlers, not computed inline (a bare `validationCallback(this)`
    // would pass this DropArea, not the drag, to the callback).
    property bool valid: false

    // Overlays `target` exactly (same parent's coordinate space) rather than
    // participating in a layout's own flow -- callers place this as a floating
    // sibling of `target`, matching qml/ActionNode.qml's existing drop-area
    // convention of a manually positioned overlay rather than a layout child.
    x: target ? target.x : 0
    y: target ? target.y : 0
    width: target ? target.width : 0
    height: target ? target.height : 0

    onEntered: (drag) => {
        root.valid = root.validationCallback === null || root.validationCallback(drag)
    }
    onExited: () => {
        root.valid = false
    }
    onDropped: (drop) => {
        if (root.valid && root.dropCallback !== null) {
            root.dropCallback(drop)
        }
    }

    Rectangle {
        id: _insertionLine

        visible: root.containsDrag && root.valid
        anchors.left: parent.left
        anchors.right: parent.right
        // Plain `y`, not a top/bottom anchor pair -- anchoring both edges alongside an
        // explicit `height` lets the anchors win and stretch this to the full row height
        // instead of staying a 2px line. `y` + a fixed `height` can't fight like that.
        // With a nonzero `gap`, centered on the gap between rows rather than flush
        // with the row edge, so it reads as sitting between the rows, not on one.
        y: root.gap <= 0
            ? (root.inTopBand ? 0 : root.height - _insertionLine.height)
            : (root.inTopBand
                ? -root.gap / 2 - _insertionLine.height / 2
                : root.height + root.gap / 2 - _insertionLine.height / 2)
        height: Metrics.hairline
        color: Theme.accent
    }
}
