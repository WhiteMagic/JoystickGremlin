// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Layouts

import Gremlin.Profile
import Kobold.Foundation
import Kobold.Internal

// Recursive replacement for legacy qml/ActionNode.qml, built from the Phase 6 Kobold.Internal
// pieces (ActionRow, TreeIndent) and this module's own RowDropBand. Lives in Kobold.Controls
// rather than Kobold.Internal because plugins with their own nested action containers (Chain,
// Condition, Tempo, ...) instantiate this directly for their own children, exactly as they
// instantiated the legacy ActionNode -- it is shared with actions, not app-only chrome.
Item {
    id: root

    required property ActionModel action
    // Optional: the action immediately before this one in the same container, used to resolve
    // a top-band drop ("insert before me") into the `dropAction(source, target, "append")`
    // primitive, which only knows how to append after a target. Left null for a first item --
    // a top-band drop there degrades to appending after this row instead of a true prepend,
    // matching legacy ActionNode's own drop support, which had no "insert at the very start"
    // path either.
    property ActionModel previousSibling: null
    // Accepted for backward compatibility only: the ~10 still-legacy container plugins
    // (Chain, Condition, ...) haven't been migrated off their existing
    // `ActionNode { action: modelData; parentAction: ...; containerName: ... }` delegate
    // declarations, and QML errors ("cannot assign to non-existent property") on any
    // property a delegate binds that the component doesn't declare. Unused here --
    // removeAction/dropAction are called on `action` itself, not the parent, since
    // `_binding_model` is shared across every ActionModel in the same tree.
    property ActionModel parentAction: null
    property string containerName: ""

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

            expanded: backend.isActionExpanded(root.action.id, root.action.sequenceIndex)
            iconPath: root.action.iconPath
            name: root.action.actionLabel
            showTriggerMode: root.action.actionBehavior === "button" &&
                root.action.canChangeActivation
            activateOnPress: root.action.activateOnPress
            activateOnRelease: root.action.activateOnRelease
            hasError: !root.action.isValid
            errorHint: root.action.userFeedback.map((hint) => hint.message).join("\n")
            dragTarget: root

            // `backend.isActionExpanded(...)` above has no NOTIFY signal, so it only ever
            // seeds `expanded`'s initial value -- it does not make the property reactive.
            // The toggle itself has to be an explicit write here, not a re-read of that
            // same (unchanging) expression.
            onToggleExpandedRequested: {
                _header.expanded = !_header.expanded
                backend.setIsActionExpanded(
                    root.action.id, root.action.sequenceIndex, _header.expanded
                )
            }
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

    // Row-edge-band drop feedback for reordering among this action's siblings (SPEC §8).
    RowDropBand {
        id: _dropBand

        target: _header

        validationCallback: function(drop) {
            return drop.getDataAsString("type") === "action" &&
                drop.getDataAsString("root") === root.action.rootActionId
        }
        dropCallback: function(drop) {
            const targetAction = (_dropBand.inTopBand && root.previousSibling) ?
                root.previousSibling : root.action
            root.action.dropAction(drop.text, targetAction.sequenceIndex, "append")
        }
    }
}
