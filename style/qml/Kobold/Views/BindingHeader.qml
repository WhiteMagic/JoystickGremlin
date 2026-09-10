// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Profile
import Kobold.Controls
import Kobold.Foundation

// Header of an action sequence, containing a drag handle, the description of the
// sequence and the ability to add actions.
Item {
    id: root

    property InputItemBindingModel inputBinding
    property InputItemModel inputItemModel

    // Ensures a drag cannot start before the image is ready.
    property bool _imageReady: false

    implicitHeight: Metrics.rowAction

    Drag.active: _dragArea.drag.active && root._imageReady
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
                    root._imageReady = false
                    root.grabToImage(function(result) {
                        root.Drag.imageSource = result.url
                        root._imageReady = true
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
