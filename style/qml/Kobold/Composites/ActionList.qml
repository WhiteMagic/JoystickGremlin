// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts

import Gremlin.Profile
import Kobold.Foundation
import Kobold.Controls

// One ActionNode per action in a container, plus the drop machinery for reordering them.
// Boundary `i` means "insert above action i"; boundary `_actions.length` is the trailing
// default target, which also serves as the sole target for an empty container.
Item {
    id: root

    required property ActionModel containerOwner
    required property string containerName

    readonly property var _actions: root.containerOwner.getActions(root.containerName)

    // The boundary this list currently owns, or -1. Derived from the global claim, so a
    // nested list's gap can never coexist with an ancestor's.
    readonly property int _activeGapIndex: DragSession.activeList === root
        ? DragSession.activeIndex
        : -1

    // Holds the dragged header plus gapS of padding either side, so the box genuinely
    // contains a row rather than tracing where its pixels would go. 36/54/72 -- integer
    // at every scale. Also the drag's hysteresis: see DragSession._switchMargin.
    readonly property real _gapOpenHeight: Metrics.rowAction + 2 * Metrics.gapS
    readonly property int _openDuration: 120
    readonly property int _closeDuration: 60

    // Repeater index of the dragged row, or -1 when the drag started in another list.
    readonly property int _draggedIndex: {
        for (let index = 0; index < _repeater.count; ++index) {
            if (_repeater.itemAt(index) === DragSession.draggedEntry) {
                return index
            }
        }
        return -1
    }

    implicitWidth: _column.implicitWidth
    implicitHeight: _column.implicitHeight

    // The drop target: a box that opens at the claimed boundary. Height is the only
    // animated property -- the box is simply clipped to whatever height exists, so it
    // unfolds without a second animator to keep in sync.
    component GapIndicator: Item {
        id: indicator

        property bool open: false
        // Dead space above the box -- the row-to-row spacing this indicator subsumes.
        property real leadingSpace: 0
        // The box region's height while unclaimed. Non-zero only for an empty container,
        // whose reserved row becomes the box instead of sitting blank above one.
        property real closedHeight: 0
        property real openHeight: root._gapOpenHeight

        property real _boxHeight: 0

        implicitHeight: indicator.leadingSpace
            + Math.max(indicator.closedHeight, indicator._boxHeight)

        // Opening and closing run at different speeds, and a Behavior cannot see which
        // way the value moved -- gating one on `enabled` races the binding it animates.
        // So the direction lives in the transition instead.
        states: State {
            name: "open"
            when: indicator.open

            PropertyChanges {
                indicator._boxHeight: indicator.openHeight
            }
        }
        transitions: [
            Transition {
                to: "open"

                NumberAnimation {
                    target: indicator
                    property: "_boxHeight"
                    duration: root._openDuration
                    easing.type: Easing.OutCubic
                }
            },
            Transition {
                to: ""

                NumberAnimation {
                    target: indicator
                    property: "_boxHeight"
                    duration: root._closeDuration
                    easing.type: Easing.OutCubic
                }
            }
        ]

        Rectangle {
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            height: indicator._boxHeight
            visible: indicator._boxHeight > 0

            color: Theme.bgAlt
            border.color: Theme.accent
            border.width: Metrics.hairline
            radius: Metrics.radius
        }
    }

    ColumnLayout {
        id: _column

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 0

        Repeater {
            id: _repeater

            model: root._actions

            delegate: Item {
                id: _entry

                required property var modelData
                required property int index

                // The dragged row's own two boundaries are no-op drops.
                readonly property bool _isNoOp: root._draggedIndex >= 0
                    && (_entry.index === root._draggedIndex
                        || _entry.index === root._draggedIndex + 1)

                Layout.fillWidth: true
                implicitWidth: _node.implicitWidth
                // _node reparents to the Overlay while this row is dragged -- hold its slot
                // open at one header so the boundaries either side of it stay put.
                implicitHeight: (DragSession.draggedEntry === _entry
                    ? Metrics.rowAction
                    : _node.implicitHeight) + _gap.implicitHeight

                // Owns boundary `index`, sitting at this row's own top and centred on it.
                // Read live, never snapshotted: the gap grows inside _gap, so a claimed
                // boundary does not move while everything below it shifts down by the gap.
                // That asymmetry is most of the hysteresis -- switching forward happens half
                // a gap later than switching back; DragSession._switchMargin only has to
                // break the exact tie on top of it.
                DropArea {
                    id: _zone

                    // Symmetric about the header. Expressed as a constant offset from the
                    // row's top rather than anchored to _gap.bottom: the indicator is what
                    // grows when this row holds the claim, and a zone that moved with it
                    // would drag itself out from under a stationary cursor.
                    readonly property real _headerCenterOffset: Metrics.actionSpacing
                        + Metrics.rowAction / 2

                    anchors.left: parent.left
                    anchors.right: parent.right
                    y: _zone._headerCenterOffset - _zone.height / 2
                    height: Metrics.rowAction * 2
                    keys: ["action"]

                    onEntered: (drag) => _zone._propose(drag)
                    onPositionChanged: (drag) => _zone._propose(drag)
                    onExited: () => DragSession.withdraw(root, _entry.index)

                    // Boundary `index` is the row's own top, which sits at -y in zone
                    // coordinates whatever the zone's placement.
                    function _propose(drag) {
                        if (_entry._isNoOp) {
                            return
                        }
                        DragSession.propose(Math.abs(drag.y + _zone.y), root, _entry.index)
                    }
                }

                // Renders boundary `index`.
                GapIndicator {
                    id: _gap

                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.right: parent.right

                    leadingSpace: Metrics.actionSpacing
                    open: root._activeGapIndex === _entry.index
                }

                // The slot this row vacated while it floats over the Overlay. Outlined
                // rather than filled, and deliberately unlike the accent-bordered target:
                // its own two boundaries are no-op drops, so it must not read as one.
                Rectangle {
                    anchors.top: _gap.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right
                    height: Metrics.rowAction
                    visible: DragSession.draggedEntry === _entry

                    color: "transparent"
                    border.color: Theme.line
                    border.width: Metrics.hairline
                    radius: Metrics.radius
                }

                ActionNode {
                    id: _node

                    anchors.top: _gap.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right

                    action: _entry.modelData
                    dragEntry: _entry
                }
            }
        }

        // Renders the trailing boundary, and is the only target when the container is empty.
        Item {
            id: _defaultTarget

            readonly property int _boundaryIndex: root._actions.length
            readonly property bool _isNoOp: root._draggedIndex >= 0
                && _defaultTarget._boundaryIndex === root._draggedIndex + 1

            Layout.fillWidth: true
            Layout.preferredHeight: _defaultGap.implicitHeight

            // An empty container's reserved row IS the box -- the box grows inside it and
            // then past it, so there is one hole rather than a blank band above a target.
            GapIndicator {
                id: _defaultGap

                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right

                leadingSpace: root._actions.length === 0 ? 0 : Metrics.hairline
                closedHeight: root._actions.length === 0 ? Metrics.rowAction : 0
                open: root._activeGapIndex === _defaultTarget._boundaryIndex
            }

            DropArea {
                id: _defaultZone

                anchors.left: parent.left
                anchors.right: parent.right
                y: -_defaultZone.height / 2
                height: Metrics.rowAction * 2
                keys: ["action"]

                onEntered: (drag) => _defaultZone._propose(drag)
                onPositionChanged: (drag) => _defaultZone._propose(drag)
                onExited: () => DragSession.withdraw(root, _defaultTarget._boundaryIndex)

                function _propose(drag) {
                    if (_defaultTarget._isNoOp) {
                        return
                    }
                    DragSession.propose(Math.abs(drag.y + _defaultZone.y),
                                        root, _defaultTarget._boundaryIndex)
                }
            }
        }
    }
}
