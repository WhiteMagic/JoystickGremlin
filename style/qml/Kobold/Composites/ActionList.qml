// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Layouts

import Gremlin.Profile
import Kobold.Foundation
import Kobold.Controls

// Replaces the old hand-wired `Repeater { delegate: ActionNode { action: modelData;
// previousSibling: ... } }` pattern duplicated at every container plugin call site. Zone
// ownership is boundary-based, not row-based: N children need N+1 drop zones. ActionNode owns
// none of them -- they all live here, so each internal boundary can be drawn above the row that
// follows it (reads as "drop above this action") rather than below the row that precedes it,
// which is where a per-row self-owned band would end up, invisible to anyone hovering the next
// row instead. Each entry below owns the boundary immediately above itself (skipped for the very
// first entry, which the leading band covers instead) and, only for the last entry, the trailing
// boundary after it -- the one zone with no "next row" to be drawn above of.
Item {
    id: root

    required property ActionModel containerOwner
    required property string containerName

    readonly property var _actions: root.containerOwner.getActions(root.containerName)

    implicitWidth: _column.implicitWidth
    implicitHeight: _column.implicitHeight

    ColumnLayout {
        id: _column

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 0

        // Zero-height anchor purely so the leading RowDropBand below has a `target` to
        // overlay even when the container is empty -- it has no visible content of its own.
        Item {
            id: _leadingAnchor

            Layout.fillWidth: true
            Layout.preferredHeight: Metrics.hairline
        }

        Repeater {
            model: root._actions

            delegate: Item {
                id: _entry

                required property var modelData
                required property int index

                // The row the boundary above this one drops after -- undefined mid-rebuild,
                // which its validationCallback must return false for rather than throw on.
                readonly property var _previousAction: root._actions[index - 1]

                Layout.fillWidth: true
                implicitWidth: _node.implicitWidth
                implicitHeight: _node.implicitHeight + _spacer.implicitHeight

                ActionNode {
                    id: _node

                    anchors.left: parent.left
                    anchors.right: parent.right

                    action: _entry.modelData
                }

                Item {
                    id: _spacer

                    anchors.top: _node.bottom
                    implicitHeight: Metrics.actionSpacing
                    implicitWidth: parent.width
                }

                // The boundary directly above this row -- disabled for the first entry,
                // whose "before me" zone is the leading band below instead (enabling both
                // here too would duplicate that zone). Targets _node (the row itself), not
                // _spacer -- edge: "top" is a band on the row's own upper edge, matching the
                // upper/lower-half-of-the-row convention; _spacer sits below this row, which
                // would put the hit area a full row too low relative to the drop index below.
                RowDropBand {
                    target: _node
                    edge: "top"
                    enabled: _entry.index > 0

                    validationCallback: function(drop) {
                        if (!_entry._previousAction) {
                            return false
                        }
                        // canAcceptDrop last -- only past the type check is `text` a sequence index.
                        return drop.getDataAsString("type") === "action" &&
                            drop.getDataAsString("root") === root.containerOwner.rootActionId &&
                            _entry._previousAction.canAcceptDrop(parseInt(drop.text))
                    }
                    dropCallback: function(drop) {
                        root.containerOwner.dropAction(
                            drop.text, _entry._previousAction.sequenceIndex, "append", "")
                    }
                }

                // The boundary after this row -- only meaningful for the last entry (every
                // other row's trailing boundary is the next row's own leading band above).
                // target: _node, not _node.headerItem -- the hit-area and the insertion line
                // both need to mark the bottom of this row's whole rendered body (including
                // any expanded nested content), not just its header, or the drop feedback and
                // the row you're actually hovering stop matching each other. A container
                // action's own nested ActionList can end up with its trailing band at this
                // same screen position; that collision is a separate, unresolved problem.
                RowDropBand {
                    target: _node
                    edge: "bottom"
                    enabled: _entry.index === root._actions.length - 1

                    validationCallback: function(drop) {
                        return drop.getDataAsString("type") === "action" &&
                            drop.getDataAsString("root") === root.containerOwner.rootActionId &&
                            _entry.modelData.canAcceptDrop(parseInt(drop.text))
                    }
                    dropCallback: function(drop) {
                        root.containerOwner.dropAction(
                            drop.text, _entry.modelData.sequenceIndex, "append", "")
                    }
                }
            }
        }
    }

    RowDropBand {
        target: _leadingAnchor
        edge: "top"

        validationCallback: function(drop) {
            return drop.getDataAsString("type") === "action" &&
                drop.getDataAsString("root") === root.containerOwner.rootActionId &&
                root.containerOwner.canAcceptDrop(parseInt(drop.text))
        }
        dropCallback: function(drop) {
            root.containerOwner.dropAction(
                drop.text, root.containerOwner.sequenceIndex, "container", root.containerName)
        }
    }
}
