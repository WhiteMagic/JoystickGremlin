// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Profile
import Kobold.Foundation
import Kobold.Controls

Item {
    id: root

    required property ActionModel action

    // Reference to this item in the containing ActionList.
    property Item dragEntry: null

    // Stores the action's expanded state before a drag event.
    property var _expandedStateToRestore: null

    // Temporary width modifiers of the dragged action such that it visually fits into
    // the drop indicators.
    property real _dragLeftInset: 0
    property real _dragRightInset: 0

    implicitWidth: _content.implicitWidth
    implicitHeight: _content.implicitHeight

    // Ensure the action is drawn above everything else during a drag.
    z: Drag.active ? 1 : 0

    // During a drag the action is collapsed to just the header and than moved by the
    // user. For the opening and closing of drop indicators to work the action item is
    // reparented to an overlay that is on top of the entire UI.
    states: State {
        // Needs root to be used, otherwise drag won't react correctly and the action
        // is not rendered correctly above everything else.
        name: "dragging"
        when: root.Drag.active

        ParentChange {
            target: root
            parent: root.Overlay.overlay
        }
        AnchorChanges {
            target: root
            anchors.top: undefined
            anchors.left: undefined
            anchors.right: undefined
        }
    }

    // Setup the drag event handling.
    // - Drag.internal is required to be able to drag an actual QML item.
    // - Drag.active is driven by the mouse handler inside the ActionRow.
    // - Drag.source is this item instanced inside the parent ActionList.
    Drag.active: _header.dragActive
    Drag.dragType: Drag.Internal
    Drag.source: root.dragEntry
    Drag.keys: ["action"]
    // The position which triggers with a drop area is positioned in the center
    // of the ActionRow to provide the same behavior when dragging up or down.
    Drag.hotSpot.x: width / 2
    Drag.hotSpot.y: _header.height / 2

    // Handle drag state change as for Drag.Internal there is no automation for it.
    Drag.onActiveChanged: {
        // The action is collapsed during the drag and resized to fit the currently
        // active drop indicator. The DragSession handler is also initialized here.
        if (Drag.active) {
            _expandedStateToRestore = action.expanded
            action.expanded = false
            _dragLeftInset = Metrics.gapS
            _dragRightInset = Metrics.gapS
            DragSession.begin(dragEntry)
        }
        // Upon terminating state is resolved here, including restoring the action's
        // expanded state and geometry.
        else {
            _dragLeftInset = 0
            _dragRightInset = 0
            if (_expandedStateToRestore !== null) {
                action.expanded = _expandedStateToRestore
                _expandedStateToRestore = null
            }
            Qt.callLater(() => { height = Qt.binding(() => implicitHeight) })
            DragSession.end()
        }
    }

    // Compute the widths used to make the header firs visually in the DragIndicator.
    function _updateHeaderInset() {
        if (!Drag.active || !DragSession.activeList) {
            return
        }
        _dragLeftInset = DragSession.activeList.mapToItem(root, 0, 0).x + Metrics.gapS
        _dragRightInset = Metrics.gapS
    }

    Connections {
        target: DragSession

        function onActiveListChanged() {
            root._updateHeaderInset()
        }
    }

    // Background used to ensure the header is visible over the background during a
    // drag event.
    Rectangle {
        id: _headerDragBackground

        anchors.fill: parent
        anchors.leftMargin: root._dragLeftInset
        anchors.rightMargin: root._dragRightInset
        visible: root.Drag.active

        color: Theme.bg
        border.color: Theme.line
        border.width: Metrics.hairline
        radius: Metrics.radius
    }

    // Layout visualizing the actual action and its contents.
    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: root._dragLeftInset
        anchors.rightMargin: root._dragRightInset
        spacing: 0

        // Header of the action, containing basic information and controls.
        ActionRow {
            id: _header

            Layout.fillWidth: true

            expanded: root.action.expanded
            iconPath: root.action.iconPath
            name: root.action.actionLabel
            showTriggerMode: root.action.actionBehavior === "button" &&
                root.action.canChangeActivation
            activateOnPress: root.action.activateOnPress
            activateOnRelease: root.action.activateOnRelease
            hasError: !root.action.isValid
            errorHint: root.action.userFeedback
                .map((hint) => { return hint.message }).join("\n")
            dragTarget: root

            onToggleExpandedRequested: { root.action.expanded = !root.action.expanded }
            onNameEdited: (text) => { root.action.actionLabel = text }
            onActivateOnPressEdited: (value) => { root.action.activateOnPress = value }
            onActivateOnReleaseEdited: (value) => {
                root.action.activateOnRelease = value
            }
            onRemoveRequested: { root.action.removeAction(root.action.sequenceIndex) }
            onDropRequested: {
                DragSession.drop(root.action.sequenceIndex)
            }
        }

        // Vertical line to the left of an action indicating its hierarchical depth.
        TreeIndent {
            Layout.fillWidth: true

            visible: _header.expanded
            hasChildren: root.action.hasChildren

            Loader {
                id: _body

                Layout.fillWidth: true

                Component.onCompleted: {
                    setSource(root.action.qmlPath, { "action": root.action })
                }
            }
        }
    }
}
