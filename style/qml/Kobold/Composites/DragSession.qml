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

    // The ActionList row (Repeater entry) currently being dragged, or null. Doubles as the
    // "am I dragging myself" identity for every other row's DropArea, and as the source for
    // the canAcceptDrop(sourceSequenceIndex) validity check (draggedEntry.modelData).
    property Item draggedEntry: null

    // The winning boundary for the current drag position: the ActionList that owns it and
    // the boundary's index within that list. Global, so exactly one gap is ever open --
    // a nested list's claim and an ancestor's cannot coexist.
    property Item activeList: null
    property int activeIndex: -1

    property var _pending: []

    function begin(entry) {
        root.draggedEntry = entry
    }

    function end() {
        root.draggedEntry = null
        root._pending = []
        root.activeList = null
        root.activeIndex = -1
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
