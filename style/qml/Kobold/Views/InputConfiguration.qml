// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Gremlin.Profile

import Kobold.Foundation
import Kobold.Controls

Item {
    id: _root

    property InputItemModel inputItemModel
    property int inputIndex

    Connections {
        target: uiState

        function onInputChanged() {
            _root.inputItemModel = backend.getInputItem(
                uiState.currentInput,
                uiState.currentInputIndex
            )
        }
    }

    Connections {
        target: signal

        function onReloadCurrentInputItem() {
            _root.inputItemModel = backend.getInputItem(
                uiState.currentInput,
                uiState.currentInputIndex
            )
        }
    }

    // Widget content
    ColumnLayout {
        id: _content

        anchors.fill: parent
        anchors.topMargin: Metrics.gapM

        // Show all actions associated with this input. SPEC §8: sequences are independent
        // trees, separated by space -- never a rule between them (InputItemBinding.qml
        // carries no padding of its own; this gapS is the entire gap on both sides of the
        // ghost row, see the delegate below).
        ScrollList {
            id: _listView

            Layout.fillHeight: true
            Layout.fillWidth: true
            // Layouts drop invisible children entirely, so the empty-state Item below
            // takes over the slot instead of leaving a blank list.
            visible: count > 0
            scrollbarAlwaysVisible: true
            spacing: Metrics.gapS

            // Content to visualize
            model: _root.inputItemModel
            delegate: _entryDelegate
            // Not reuseItems: true -- that's for the ~100 shallow, uniform rows of the
            // left-pane input list (kobold-qml.md). Here each row is a handful of deep,
            // recursively Loader-built action trees of wildly different shape; recycling
            // one into another meant a full synchronous subtree rebuild mid-scroll (see
            // InputItemBinding.qml's onInputBindingChanged), and the delegate's height
            // binding lagged that rebuild by a frame -- with a mouse wheel's coalesced
            // multi-notch events landing several recycles at once, that read as the list
            // bouncing.
            reuseItems: false

            // The boundary before the first sequence -- reordering whole sequences reuses
            // the same boundary-owned RowDropBand mechanism as the action tree (SPEC §8);
            // this is the one zone with no preceding entry to attach to, so it lives on the
            // ListView's own header instead of inside a delegate.
            header: Item {
                id: _leadingWrapper

                width: _listView.width
                height: Metrics.gapL

                Item {
                    id: _leadingAnchor
                    anchors.fill: parent
                }

                RowDropBand {
                    target: _leadingAnchor
                    edge: "top"

                    validationCallback: function(drop) {
                        return drop.getDataAsString("type") === "sequence"
                    }
                    dropCallback: function(drop) {
                        _root.inputItemModel.dropAction(drop.text, "", true)
                    }
                }
            }
        }

        // ListView delegate definition rendering individual bindings via ActionTree
        // instances, each followed by a ghost "New Action Sequence" trigger -- repeating
        // it after every sequence breaks the list up visually and keeps it reachable
        // wherever the user is scrolled, rather than only at the very bottom.
        Component {
            id: _entryDelegate

            Item {
                id: _delegate

                height: _sequenceColumn.height
                width: view.width

                property ListView view: ListView.view

                ColumnLayout {
                    id: _sequenceColumn

                    width: parent.width
                    spacing: Metrics.gapS

                    InputItemBinding {
                        id: _binding

                        Layout.fillWidth: true

                        inputBinding: modelData
                        inputItemModel: _root.inputItemModel
                    }

                    // Ghost trigger: a permanent `line` hairline through the middle reads as
                    // a divider between sequences, not just a plain button -- an `fg` edge
                    // on hover adds feedback on top of that, never accent, never a fill.
                    ToolButton {
                        id: _ghostRow

                        Layout.fillWidth: true
                        Layout.leftMargin: Metrics.gapM
                        Layout.rightMargin: Metrics.gapM * 2
                        implicitHeight: Metrics.rowAction

                        text: "New Action Sequence"

                        background: Item {
                            // Hidden on hover -- alongside the hover border below, the
                            // center line reads as clutter rather than a second cue.
                            Rectangle {
                                visible: !(_ghostRow.hovered || _ghostRow.down)
                                anchors.verticalCenter: parent.verticalCenter
                                width: parent.width
                                height: Metrics.hairline
                                color: Theme.line
                            }

                            // Breaks the hairline under the label instead of striking
                            // through it -- matches the window's own bg (Main.qml), not
                            // the panel, since this row has no fill of its own.
                            Rectangle {
                                visible: !(_ghostRow.hovered || _ghostRow.down)
                                anchors.centerIn: parent
                                width: _ghostContent.implicitWidth + Metrics.gapM * 2
                                height: parent.height
                                color: Theme.bg
                            }

                            Rectangle {
                                anchors.fill: parent
                                radius: 0
                                color: "transparent"
                                border.width: Metrics.hairline
                                border.color: (_ghostRow.hovered || _ghostRow.down) ?
                                    Theme.line : "transparent"
                            }
                        }

                        contentItem: Item {
                            implicitWidth: _ghostContent.implicitWidth
                            implicitHeight: Metrics.controlHeight

                            Row {
                                id: _ghostContent

                                anchors.centerIn: parent
                                spacing: Metrics.gapS

                                AppIcon {
                                    anchors.verticalCenter: parent.verticalCenter
                                    name: "plus"
                                    role: (_ghostRow.hovered || _ghostRow.down) ?
                                        "fg" : "fgMuted"
                                }

                                Text {
                                    anchors.verticalCenter: parent.verticalCenter
                                    text: _ghostRow.text
                                    color: (_ghostRow.hovered || _ghostRow.down) ?
                                        Theme.fg : Theme.fgMuted
                                    font.family: FontType.sans
                                    font.pixelSize: Metrics.textDetail
                                }
                            }
                        }

                        onClicked: {
                            _root.inputItemModel.newActionSequence()
                        }
                    }
                }

                // The boundary after this sequence -- doubles as "before the next sequence"
                // for every entry but the last (the first entry's "before me" zone is the
                // ListView's leading header band instead). Lives on this sequence's own
                // ghost row rather than a gap, so the drop feedback centers on the row that
                // means the same thing ("insert a sequence here").
                RowDropBand {
                    target: _ghostRow
                    coverTarget: true

                    validationCallback: function(drop) {
                        return drop.getDataAsString("type") === "sequence"
                    }
                    dropCallback: function(drop) {
                        _root.inputItemModel.dropAction(drop.text, modelData.rootAction.id, false)
                    }
                }
            }
        }

        // Nothing mapped to this input yet -- a large, still-unfilled invite (SPEC §8:
        // an ordinary push button, not filled), vertically centered in the space the
        // list would otherwise fill.
        Item {
            Layout.fillHeight: true
            Layout.fillWidth: true
            visible: _listView.count === 0

            ColumnLayout {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: Metrics.gapM
                anchors.rightMargin: Metrics.gapM
                spacing: Metrics.gapS

                Button {
                    id: _emptyStateButton

                    Layout.fillWidth: true
                    Layout.preferredHeight: Metrics.rowInput

                    text: "New Action Sequence"

                    contentItem: Item {
                        implicitWidth: _emptyStateContent.implicitWidth
                        implicitHeight: Metrics.controlHeight

                        Row {
                            id: _emptyStateContent

                            anchors.centerIn: parent
                            spacing: Metrics.gapS

                            AppIcon {
                                anchors.verticalCenter: parent.verticalCenter
                                name: "plus"
                                role: _emptyStateButton.enabled ? "fg" : "fgDisabled"
                            }

                            Text {
                                anchors.verticalCenter: parent.verticalCenter
                                text: _emptyStateButton.text
                                color: _emptyStateButton.enabled ? Theme.fg : Theme.fgDisabled
                                font: _emptyStateButton.font
                            }
                        }
                    }

                    onClicked: {
                        _root.inputItemModel.newActionSequence()
                    }
                }

                Text {
                    Layout.alignment: Qt.AlignHCenter

                    text: "Nothing mapped to this input yet"
                    color: Theme.fgMuted
                    font.family: FontType.sans
                    font.pixelSize: Metrics.textDetail
                }
            }
        }
    }
}
