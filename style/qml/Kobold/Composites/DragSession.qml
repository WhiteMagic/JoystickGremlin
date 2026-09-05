// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma Singleton

import QtQuick

import Kobold.Foundation

// Global drag-session state for the action tree: at most one ActionNode is ever being
// dragged at a time across the whole app, no matter how many ActionLists exist (one per
// container, arbitrarily nested), so this state belongs to the drag itself, not to any one
// row's delegate. A singleton is what makes it reachable from any ActionList's DropArea --
// including a sibling or ancestor container list the drag moves into -- without threading a
// reference down through every nested container.
QtObject {
    id: root

    // The ActionList row (Repeater entry) currently being dragged, or null. Serves as the
    // "am I dragging myself" identity for every other row's DropArea. Identity only -- the
    // dragged node hands its own sequence index to commit() rather than having this reached
    // through for it.
    property Item draggedEntry: null

    // The winning boundary for the current drag position: the ActionList that owns it and
    // the boundary's index within that list. Global, so exactly one gap is ever open --
    // a nested list's claim and an ancestor's cannot coexist.
    property ActionList activeList: null
    property int activeIndex: -1

    property var _pending: []

    // The drop taken at mouse-release, or null. Snapshotted rather than read back later
    // because cancelling an internal drag sends a DragLeave first, which withdraws the
    // claim before Drag.active's own handlers ever run.
    property var _committed: null

    function begin(entry) {
        root.draggedEntry = entry
    }

    // Called from the drag handle's release, while the claim is still live. Returns whether
    // a drop was taken, so the dragged node knows not to reload on top of the rebuild.
    function commit(sourceSequenceIndex) {
        // A proposal delivered in this same pass is still queued behind Qt.callLater; flush
        // it so the claim reflects where the cursor actually ended.
        root._resolve()
        if (!root.draggedEntry || !root.activeList || root.activeIndex < 0) {
            return false
        }
        root._committed = {
            owner: root.activeList.containerOwner,
            container: root.activeList.containerName,
            position: root.activeIndex,
            source: sourceSequenceIndex
        }
        return true
    }

    function end() {
        const committed = root._committed
        root.draggedEntry = null
        root._pending = []
        root.activeList = null
        root.activeIndex = -1
        root._committed = null

        // dropAction rebuilds every ActionModel and tears down the dragged node's own QML
        // items. Running that inside the mouse-release handler that triggered it destroys
        // the object graph mid-event.
        if (committed) {
            Qt.callLater(() => committed.owner.dropAction(
                committed.source, committed.container, committed.position))
        }
    }

    // Drop zones overlap by design and Qt delivers a drag event to every one of them in no
    // defined order, so a running best would depend on who ran first. Qt.callLater collapses
    // the whole delivery pass into one _resolve that sees every candidate.
    function propose(distance, list, index) {
        root._pending.push({distance, list, index})
        Qt.callLater(root._resolve)
    }

    function withdraw(list, index) {
        if (root.activeList === list && root.activeIndex === index) {
            root.activeList = null
            root.activeIndex = -1
        }
    }

    // How much closer a challenger has to be before it takes the claim. Two adjacent zones
    // both cover the midpoint between their boundaries and propose equal distances there, so
    // without a margin the winner comes down to delivery order and a sub-pixel wobble flips
    // the gap back and forth.
    //
    // Most of the damping comes from the open gap's own geometry, not from here (see
    // ActionList's _gapOpenHeight) -- this only has to out-measure that sub-pixel wobble.
    readonly property real _switchMargin: Metrics.gapS

    function _resolve() {
        let best = null
        let incumbent = null
        for (const proposal of root._pending) {
            if (!best || proposal.distance < best.distance) {
                best = proposal
            }
            if (proposal.list === root.activeList && proposal.index === root.activeIndex) {
                incumbent = proposal
            }
        }
        root._pending = []
        if (!best) {
            return
        }
        // An incumbent that stopped proposing has had its zone left entirely, so the best
        // challenger takes over with no margin to clear.
        if (incumbent && best.distance > incumbent.distance - root._switchMargin) {
            return
        }
        root.activeList = best.list
        root.activeIndex = best.index
    }
}
