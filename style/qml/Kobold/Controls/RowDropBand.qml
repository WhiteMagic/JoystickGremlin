// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick

import Kobold.Foundation

// Simple single accent-colored line used to indicate where the dragged element will be
// dropped. The DropArea covers the entire space of the given target, but renders the
// indicator line only on the specified edge.
DropArea {
    id: root

    // Target item to apply the DragArea to and drag & drop callback handlers.
    property Item target: null
    property var validationCallback: null
    property var dropCallback: null

    // Additional spacing forced by the DropArea.
    property real gap: 0
    // Which edge of target the indicator should appear, "bottom" or "top".
    property string edge: "bottom"
    // If true the DropArea is extended to cover the given target. Otherwise it is
    // limited to purely the indicator line.
    property bool coverTarget: false
    // Holds the validity of the drag event.
    property bool valid: false

    // Compute the extent and position of the DropArea based on the configuration.
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
        // Renders the indicator line at the correct spot based on the configuration.
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
