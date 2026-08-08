// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kobold.Foundation
import Kobold.Controls

import Gremlin.Profile

// SPEC §8 binding header: [grip][description][Treat as][Add action, bordered][!][x]. Live
// replacement for the general header row of the legacy
// qml/InputItemBindingConfigurationHeader.qml. The axis/hat virtual-button UI is not part of
// this row's grammar (SPEC §8 doesn't mention it) -- it stays a sibling Loader in
// qml/InputItemBinding.qml, unchanged.
// The grip is a real drag handle for whole-sequence reordering (InputConfiguration.qml owns
// the drop zones); the ghost image is this row alone, never the tree below it -- a sequence's
// action tree can be very tall and the drag visual must stay compact.
Item {
    id: root

    property InputItemBindingModel inputBinding
    property InputItemModel inputItemModel

    implicitHeight: Metrics.rowAction

    Drag.active: _dragArea.drag.active
    Drag.dragType: Drag.Automatic
    Drag.supportedActions: Qt.MoveAction
    Drag.proposedAction: Qt.MoveAction
    Drag.mimeData: ({
        "text/plain": root.inputBinding && root.inputBinding.rootAction ?
            root.inputBinding.rootAction.id : "",
        "type": "sequence"
    })
    Drag.onDragFinished: function(dropAction) {
        if (dropAction === Qt.IgnoreAction) {
            signal.reloadCurrentInputItem()
        }
    }

    function _maxSeverity(hints) {
        let highest = 0
        for (let i = 0; i < hints.length; i++) {
            if (hints[i]["type"] > highest) {
                highest = hints[i]["type"]
            }
        }
        return highest
    }

    RowLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        spacing: Metrics.gapM

        AppIcon {
            id: _grip

            name: "grip"
            role: "fgMuted"

            MouseArea {
                id: _dragArea

                anchors.fill: parent
                cursorShape: Qt.OpenHandCursor
                drag.target: root
                drag.axis: Drag.YAxis

                onPressed: {
                    root.grabToImage(function(result) {
                        root.Drag.imageSource = result.url
                    })
                }
            }
        }

        TextField {
            id: _description

            Layout.fillWidth: true
            placeholderText: "Description"
            text: root.inputBinding && root.inputBinding.rootAction ?
                root.inputBinding.rootAction.actionLabel : ""

            onEditingFinished: {
                root.inputBinding.rootAction.actionLabel = text
            }
        }

        InputBehavior {
            inputBinding: root.inputBinding
        }

        AddActionMenuButton {
            variant: "bordered"
            model: root.inputBinding && root.inputBinding.rootAction ?
                root.inputBinding.rootAction.compatibleActions : []

            onActionRequested: (name) => {
                root.inputBinding.rootAction.appendAction(name, "children")
            }
        }

        AppIcon {
            id: _feedbackIcon

            visible: root.inputBinding && root.inputBinding.userFeedback.length > 0
            name: "warning"
            role: root.inputBinding && root._maxSeverity(root.inputBinding.userFeedback) >= 3 ?
                "error" : "warning"

            HoverHandler {
                id: _feedbackHover
            }

            ToolTip.visible: _feedbackHover.hovered
            ToolTip.text: root.inputBinding ?
                root.inputBinding.userFeedback.map((h) => h.message).join("\n") : ""
        }

        ToolButton {
            icon.name: "delete"

            onClicked: {
                root.inputItemModel.deleteActionSequnce(root.inputBinding)
            }
        }
    }
}
