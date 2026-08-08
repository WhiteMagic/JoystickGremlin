// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import Kobold.Foundation

// SPEC §8 drag & drop feedback: one instance = one boundary. `edge` fixes which side of
// `target` this band owns -- no drag-position split within an instance; callers place one
// instance per boundary (N+1 for N siblings). Feedback is always exactly a 2px insertion
// line in `accent`. No parting animation -- the drag ghost + insertion line is enough.
// `coverTarget` is the one exception: the boundary IS a row, not a seam between rows -- the
// whole row gets a flat `bg` fill and the line centers instead of sitting at an edge.
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
    // Which edge of `target` this instance's hit-area and insertion line sit at.
    property string edge: "bottom"
    // When true, the hit-area is `target`'s whole rect, not one edge band -- for a drop
    // target that IS a row (e.g. the "+ New Action Sequence" ghost button), not a seam
    // between rows. `edge` is ignored in this mode; the fill below and the centered line
    // replace the edge-flush insertion line as the feedback.
    property bool coverTarget: false

    // Mime data is only reachable from the DragEvent handed to onEntered/onDropped, not
    // from any DropArea property -- so validity has to be tracked as mutable state
    // updated from those handlers, not computed inline (a bare `validationCallback(this)`
    // would pass this DropArea, not the drag, to the callback).
    property bool valid: false

    // Hit-area covers only this instance's edge band of `target`, not the whole row -- a
    // second instance owns the other edge. Positioned as target's floating sibling (manual
    // overlay, not layout child), matching qml/ActionNode.qml's existing drop-area convention.
    x: target ? target.x : 0
    y: target
        ? (root.coverTarget
            ? target.y
            : (root.edge === "top" ? target.y : target.y + target.height - Metrics.gapL))
        : 0
    width: target ? target.width : 0
    height: root.coverTarget ? (target ? target.height : 0) : Metrics.gapL

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

    // coverTarget-only: the boundary IS the row, so the whole row highlights rather than
    // a thin edge line.
    Rectangle {
        visible: root.coverTarget && root.containsDrag && root.valid
        anchors.fill: parent
        color: Theme.bg
    }

    Rectangle {
        id: _insertionLine

        visible: root.containsDrag && root.valid
        anchors.left: parent.left
        anchors.right: parent.right
        // Plain `y`, not a top/bottom anchor pair -- anchoring both edges alongside an
        // explicit `height` lets the anchors win and stretch this to the full row height
        // instead of staying a 2px line. `y` + a fixed `height` can't fight like that.
        // coverTarget centers the line in the row instead of pinning it to an edge.
        // With a nonzero `gap`, centered on the gap between rows rather than flush
        // with the row edge, so it reads as sitting between the rows, not on one.
        // With zero gap, rows are flush, so a `gapS` inset off the shared edge keeps
        // the line off the neighboring row instead of stuck to it.
        y: root.coverTarget
            ? (root.height - _insertionLine.height) / 2
            : (root.gap <= 0
                ? (root.edge === "top" ? Metrics.gapS : root.height - _insertionLine.height - Metrics.gapS)
                : (root.edge === "top"
                    ? -root.gap / 2 - _insertionLine.height / 2
                    : root.height + root.gap / 2 - _insertionLine.height / 2))
        height: Metrics.hairline
        color: Theme.accent
    }
}
