// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
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

    implicitWidth: _column.implicitWidth
    implicitHeight: _column.implicitHeight

    Drag.active: _header.dragActive
    Drag.dragType: Drag.Automatic
    Drag.supportedActions: Qt.MoveAction
    Drag.proposedAction: Qt.MoveAction
    Drag.mimeData: ({
        "text/plain": root.action.sequenceIndex,
        "type": "action",
        "root": root.action.rootActionId
    })
    Drag.onDragFinished: function(dropAction) {
        if (dropAction === Qt.IgnoreAction) {
            signal.reloadCurrentInputItem()
        }
    }

    ColumnLayout {
        id: _column

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 0

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
                root.grabToImage(function(result) {
                    root.Drag.imageSource = result.url
                })
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
