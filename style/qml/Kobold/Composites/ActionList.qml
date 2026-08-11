// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts

import Gremlin.Profile
import Kobold.Foundation
import Kobold.Controls

// Renders individual actions and provide support for drag & drop.
Item {
    id: root

    required property ActionModel containerOwner
    required property string containerName

    readonly property var _actions: containerOwner.getActions(containerName)

    // Index of the shown drop indicator, or -1 if this list is not active.
    readonly property int _activeDropIndex: DragSession.activeList === root
        ? DragSession.activeIndex
        : -1

    // Drop indicator opening and closing animation durations in milliseconds.
    readonly property int _openDuration: 120
    readonly property int _closeDuration: 60

    implicitWidth: _content.implicitWidth
    implicitHeight: _content.implicitHeight

    // Main container that holds the actual content of the list.
    ColumnLayout {
        id: _content

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

                Layout.fillWidth: true
                implicitWidth: _node.implicitWidth
                // Compute the height needed for this item. During a drag, the item
                // being dragged is hidden from the list view.
                implicitHeight: (DragSession.draggedEntry === _entry
                    ? 0
                    : _node.implicitHeight) + _dropIndicator.implicitHeight

                DropArea {
                    id: _dropArea

                    // Desired overhand of the drop area over the action header.
                    readonly property real _overhang: Metrics.rowAction / 2

                    anchors.left: parent.left
                    anchors.right: parent.right
                    // Position the area such that it is centered on the action's header
                    // and covers _overhand space above and below it.
                    y: Metrics.actionSpacing - _overhang
                    height: Metrics.rowAction + 2 * _overhang
                    keys: ["action"]

                    onEntered: (drag) => { _propose(drag) }
                    onPositionChanged: (drag) => { _propose(drag) }
                    onExited: () => { DragSession.removeDropAreaCandidate(root, _entry.index) }

                    // Sends this drop area to the DragSession to decide which
                    // indicator is selected.
                    function _propose(drag) {
                        DragSession.addDropAreaCandidate(
                            Math.abs(drag.y + y),
                            root,
                            _entry.index
                        )
                    }
                }

                // Visualizes the action's drop area.
                DropIndicator {
                    id: _dropIndicator

                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.right: parent.right

                    topSpacing: Metrics.actionSpacing
                    isOpen: root._activeDropIndex === _entry.index
                }

                // Visualize the action itself including the possible child
                // actions within.
                ActionNode {
                    id: _node

                    anchors.top: _dropIndicator.bottom
                    anchors.left: parent.left
                    anchors.right: parent.right

                    action: _entry.modelData
                    dragEntry: _entry
                }
            }
        }

        // Drop target at the bottom of a list, allowing insertion into an empty
        // list or at the end of one. This only becomes visible during an active
        // drag event.
        Item {
            id: _defaultTarget

            Layout.fillWidth: true
            Layout.preferredHeight: _defaultIndicator.implicitHeight

            DropIndicator {
                id: _defaultIndicator

                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right

                topSpacing: 0
                closedHeight: DragSession.active ? Metrics.rowAction : 0
                isOpen: root._activeDropIndex === root._actions.length
            }

            DropArea {
                id: _defaultDropArea

                anchors.left: parent.left
                anchors.right: parent.right
                // Position the drop area such that it's centered on the visual
                // indicator and then overhangs symmetrically on top and bottom.
                anchors.verticalCenter: parent.top
                anchors.verticalCenterOffset: _defaultIndicator.closedHeight / 2
                height: Metrics.rowAction * 2
                keys: ["action"]

                onEntered: (drag) => { _propose(drag) }
                onPositionChanged: (drag) => { _propose(drag) }
                onExited: () => { DragSession.removeDropAreaCandidate(root, root._actions.length) }

                function _propose(drag) {
                    DragSession.addDropAreaCandidate(
                        Math.abs(drag.y - height / 2),
                        root, root._actions.length)
                }
            }
        }
    }

    // Visualizes the area an action can be dropped into. Animates open and closed
    // based on if this "slot" is the one under consideration.
    component DropIndicator: Item {
        id: indicator

        // Indicates if the gap is open or closed.
        property bool isOpen: false
        // Empty space separating the box from the row above it, acting as a top margin.
        property real topSpacing: 0
        // Vertical space reserved for the indicator when closed.
        property real closedHeight: 0
        // Vertical space reserved for the indicator when fully open.
        property real openHeight: Metrics.rowAction + 2 * Metrics.gapS
        // Value of the animated height that the visual drop target has.
        property real _boxHeight: 0

        implicitHeight: topSpacing + Math.max(closedHeight, _boxHeight)

        // Animation of the visible indicator to open and close as it is triggered.
        states: State {
            name: "open"
            when: indicator.isOpen

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

        // Visual indicator for a possible, but not active, drop slot with that has
        // no associated action header.
        Item {
            id: _emptyDropIndicator

            anchors.left: parent.left
            anchors.right: parent.right
            y: indicator.topSpacing + (indicator.closedHeight - height) / 2
            height: Metrics.gapM
            // The closedHeight of such a slot is non zero, while for an action linked
            // slot it is 0.
            visible: indicator.closedHeight > 0 && DragSession.active
                && indicator._boxHeight <= 0

            // Sequence of three boxes which draw the following visual: |---------|
            Rectangle {
                anchors.left: parent.left
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: Metrics.hairline

                color: Theme.line
            }

            Rectangle {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                height: Metrics.hairline

                color: Theme.line
            }

            Rectangle {
                anchors.right: parent.right
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                width: Metrics.hairline

                color: Theme.line
            }
        }

        // Visual indicator for a drop slot.
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
}
