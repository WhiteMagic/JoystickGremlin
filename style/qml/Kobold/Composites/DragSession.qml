// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma Singleton

import QtQuick

import Kobold.Foundation

// Holds information about the active drag event.
//
// There is only ever one active drag event. However, the drag may hit multiple drop
// areas at the same time due to the nesting of actions. This is resolved by picking
// the drop area that's the closest to the mouse cursor with hysterisis prevention.
//
// As Qt does not emit a drop event for Drag.Internal drag mode, the drop event is
// internally cached here to dispatch to the model once the drag ends successfully.
QtObject {
    id: root

    // Action item being dragged.
    property Item draggedEntry: null

    // Indicates if a drag is active.
    readonly property bool active: draggedEntry !== null

    // Holds the ActionList that holds the currently active drop area.
    property ActionList activeList: null
    property int activeIndex: -1

    // Holds the drop areas from which the activeList and activeIndex are derived.
    property var _dropAreaCandidates: []

    // Holds the data needed to perform a drop action once the drag event ends.
    property var _dropData: null

    // Start a drag session.
    function begin(entry) {
        draggedEntry = entry
    }

    function drop(sourceSequenceIndex) {
        // Ensure the selection of the active drop area is up to date, then record the
        // drop data.
        _updateActiveDropArea()
        if (!draggedEntry || !activeList || activeIndex < 0) {
            return false
        }
        _dropData = {
            owner: activeList.containerOwner,
            container: activeList.containerName,
            position: activeIndex,
            source: sourceSequenceIndex
        }
    }

    function end() {
        // Execute the model's drop action once the drag event completes successfully.
        if (_dropData) {
            const dropDataCopy = _dropData
            Qt.callLater(() => {
                dropDataCopy.owner.dropAction(
                    dropDataCopy.source, dropDataCopy.container, dropDataCopy.position)
            })
        }

        // Reset the drag session state.
        draggedEntry = null
        _dropAreaCandidates = []
        activeList = null
        activeIndex = -1
        _dropData = null
    }

    // Multiple drop areas may fire drag events at the same time. They are recorded to
    // pick the best one once all drag events are processed.
    function addDropAreaCandidate(distance, list, index) {
        _dropAreaCandidates.push({distance, list, index})
        Qt.callLater(_updateActiveDropArea)
    }

    // Removes a drop area candidate by unsetting it in case it was the active one. This
    // works as the next update will invalidate the candidate list.
    function removeDropAreaCandidate(list, index) {
        if (activeList === list && activeIndex === index) {
            activeList = null
            activeIndex = -1
        }
    }

    // Determine the best drop area based on the distance of the mouse cursor to
    // available candidates.
    function _updateActiveDropArea() {
        // Find the entries corresponding to the current slot and the best slot based
        // on distance.
        let bestChoice = null
        let currentChoice = null
        for (const entry of _dropAreaCandidates) {
            if (!bestChoice || entry.distance < bestChoice.distance) {
                bestChoice = entry
            }
            if (entry.list === activeList && entry.index === activeIndex) {
                currentChoice = entry
            }
        }
        _dropAreaCandidates = []
        if (!bestChoice) {
            return
        }

        // Handle hysterisis by only switching to a new drop area once the current
        // selection is worse by an amount of switchMargin.
        const switchMargin = Metrics.gapS
        if (currentChoice && bestChoice.distance > currentChoice.distance - switchMargin) {
            return
        }
        activeList = bestChoice.list
        activeIndex = bestChoice.index
    }
}
