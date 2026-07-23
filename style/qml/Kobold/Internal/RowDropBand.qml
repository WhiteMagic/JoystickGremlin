// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import Kobold.Foundation

// SPEC §8 drag & drop feedback: drop targets are row-edge bands -- the upper/lower ~12px of
// a row, independent of the gap between rows, not "gap-dwellers". Feedback is a 2px
// insertion line in `line`, never accent. No parting animation -- the drag ghost + insertion
// line is enough.
//
// Same shape as the legacy qml/DragDropArea.qml (validationCallback/dropCallback props) so a
// future call-site swap is drop-in, but restyled to the SPEC's edge-band + insertion-line
// convention instead of a fixed drop zone below the row.
DropArea {
    id: root

    property Item target: null
    property var validationCallback: null
    property var dropCallback: null

    readonly property real bandHeight: Metrics.gapL
    readonly property bool inTopBand: containsDrag && drag.y < bandHeight
    readonly property bool valid: validationCallback === null || validationCallback(this)

    // Overlays `target` exactly (same parent's coordinate space) rather than
    // participating in a layout's own flow -- callers place this as a floating
    // sibling of `target`, matching qml/ActionNode.qml's existing drop-area
    // convention of a manually positioned overlay rather than a layout child.
    x: target ? target.x : 0
    y: target ? target.y : 0
    width: target ? target.width : 0
    height: target ? target.height : 0

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
        anchors.top: root.inTopBand ? parent.top : undefined
        anchors.bottom: root.inTopBand ? undefined : parent.bottom
        height: Metrics.insertionLine
        color: Theme.line
    }
}
