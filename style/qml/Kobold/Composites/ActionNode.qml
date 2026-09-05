// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Profile
import Kobold.Foundation
import Kobold.Controls

// Recursive replacement for legacy qml/ActionNode.qml, built from the Phase 6 ActionRow/TreeIndent
// pieces. Lives in Kobold.Composites, plugin-importable, because plugins with their own nested
// action containers (Chain, Condition, Tempo, ...) instantiate this directly for their own
// children, exactly as they instantiated the legacy ActionNode -- it is shared with actions, not
// app-only chrome. Purely a draggable row + recursive body -- it owns no drop zones of its own;
// ActionList (its only caller) owns every boundary band for the list this node sits in.
Item {
    id: root

    required property ActionModel action

    // Set by ActionList when instantiating this node: the owning Repeater entry.
    // Reported to the global DragSession singleton (Kobold.Composites) on drag start/end
    // so every row's DropArea -- in this list or a sibling/ancestor container's -- can
    // identify "is this the row being dragged" and look up its ActionModel for
    // canAcceptDrop, without needing a reference threaded down to it.
    property Item dragEntry: null

    // Auto-collapse while dragging so a node with expanded children doesn't drag at
    // full height. Restored unconditionally on Drag.onDragFinished -- a same-position
    // drop doesn't change sequenceIndex, so a restore gated on drop success would
    // leave it stuck collapsed.
    property bool _wasExpanded: true
    property bool _collapsedForDrag: false

    // The floating node keeps the width and scene x it had in the list, so its own border
    // lands on the drop indicator's on both sides. Inset the painted row instead of
    // resizing root: ParentChange owns root's geometry while dragging and the restored
    // anchors own it after, so neither would keep a width set here -- and Drag.hotSpot,
    // read off root.width, stays where it is. gapS matches the padding the gap box already
    // leaves above and below the header (ActionList's _gapOpenHeight).
    readonly property real _dragInset: root.Drag.active ? Metrics.gapS : 0

    implicitWidth: _column.implicitWidth
    implicitHeight: _column.implicitHeight

    // Paint above everything while floating (Overlay.overlay already draws above the
    // whole window, but z still matters for stacking against other overlay content).
    z: root.Drag.active ? 1 : 0

    // Escapes every ColumnLayout between here and the window, not just this row's own
    // ActionList -- a gap opening ANYWHERE in the tree can reflow an ancestor ColumnLayout
    // this node's position ultimately derives from, arbitrarily many levels up (containers
    // nest arbitrarily deep). Reparenting only to this node's own immediate ActionList's
    // root would escape that list's own internal reflow but not reflow further up the
    // chain, since a gap in an outer/sibling list can still push this node's whole
    // ancestor subtree around. Overlay.overlay is the only thing immune to all of it.
    // Ported from debug/attempt2.qml's `content`/`window.contentItem` reparenting -- no
    // x/y given to ParentChange, so it preserves root's current scene position across the
    // reparent instead of snapping to (0, 0) for a frame.
    //
    // All three anchors must clear, not just left/right: ActionList anchors this node's
    // `top` to its row spacer, and the drag is Drag.YAxis -- leaving `top` bound pins `y`,
    // the node can't translate, and the drag hotSpot stays parked over its home row's
    // DropArea (the one case ActionList's onEntered deliberately ignores), so no other row
    // ever sees an enter event.
    states: State {
        name: "dragging"
        when: root.Drag.active

        ParentChange {
            target: root
            // Qualified on root: an unqualified `Overlay.overlay` here attaches to the
            // ParentChange, which is neither an Item nor a Popup, so it resolves to null
            // and the reparent silently does nothing -- leaving the node in the layout to
            // be shoved around by every gap that opens above it.
            parent: root.Overlay.overlay
        }
        AnchorChanges {
            target: root
            anchors.top: undefined
            anchors.left: undefined
            anchors.right: undefined
        }
    }

    Drag.active: _header.dragActive
    Drag.dragType: Drag.Internal
    Drag.source: root.dragEntry
    Drag.keys: ["action"]
    // Leading edge of the node leads the drag: bottom edge moving down, top
    // edge moving up. root.height is just the header while dragging, since
    // onDragRequested below collapses the node first.
    //
    // Reaches Metrics.actionSpacing past that edge, out into the row-to-row gap, rather
    // than sitting exactly on it. Drag.hotSpot is only a sample point, not clamped to the
    // dragged item's own bounds, so this is legal -- and necessary: each row's DropArea is
    // capped to header height (see ActionList.qml), so without the reach, the leading edge
    // would have to travel the full visual gap before the neighboring row's drop zone even
    // starts noticing it, making the trigger feel late/unresponsive.
    Drag.hotSpot.x: root.width / 2
    Drag.hotSpot.y: _header.height / 2
    Drag.onActiveChanged: {
        if (root.Drag.active) {
            DragSession.begin(root.dragEntry)
        } else {
            DragSession.end()
        }
    }
    Drag.onDragFinished: function(dropAction) {
        if (root._collapsedForDrag) {
            root.action.expanded = root._wasExpanded
            root._collapsedForDrag = false
        }
        if (dropAction === Qt.IgnoreAction) {
            signal.reloadCurrentInputItem()
        }
    }

    // Only surface in the app that floats: while dragging this node paints over the list
    // rather than in it, and ActionRow has no fill of its own, so without this the header's
    // text and icons render straight onto whatever they pass over. 1px border + opaque
    // fill, never a shadow. Declared before _column so it stacks beneath the row.
    Rectangle {
        anchors.fill: parent
        anchors.leftMargin: root._dragInset
        anchors.rightMargin: root._dragInset
        visible: root.Drag.active

        color: Theme.bg
        border.color: Theme.line
        border.width: Metrics.hairline
        radius: Metrics.radius
    }

    ColumnLayout {
        id: _column

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: root._dragInset
        anchors.rightMargin: root._dragInset
        spacing: 0

        // Header of an action indicating it's type and providing drag handle.
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
            errorHint: root.action.userFeedback.map((hint) => hint.message).join("\n")
            dragTarget: root

            onToggleExpandedRequested: root.action.expanded = !root.action.expanded
            onNameEdited: (text) => { root.action.actionLabel = text }
            onActivateOnPressEdited: (value) => { root.action.activateOnPress = value }
            onActivateOnReleaseEdited: (value) => { root.action.activateOnRelease = value }
            onRemoveRequested: root.action.removeAction(root.action.sequenceIndex)
            onDragRequested: {
                root._wasExpanded = root.action.expanded
                root.action.expanded = false
                root._collapsedForDrag = true
            }
        }

        TreeIndent {
            Layout.fillWidth: true

            visible: _header.expanded
            hasChildren: root.action.hasChildren

            Loader {
                id: _body

                Layout.fillWidth: true

                // Not `source:` + assign-in-onLoaded -- the loaded body's own root
                // declares `required property ActionModel action`, and a required
                // property only counts as initialized if it's supplied as part of the
                // object's creation. setSource()'s initial-properties argument does
                // that; a plain post-creation assignment in onLoaded does not, and
                // throws "Required property ... was not initialized".
                Component.onCompleted: {
                    setSource(root.action.qmlPath, { "action": root.action })
                }
            }
        }
    }
}
