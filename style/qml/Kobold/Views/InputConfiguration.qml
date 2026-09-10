// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Gremlin.Profile
import Kobold.Controls
import Kobold.Foundation

// Shows all action sequences associated with a single input.
Item {
    id: _root

    property InputItemModel inputItemModel
    property int inputIndex

    // Ensure the content is updated and refreshed as needed when UI changes happen.
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

    ColumnLayout {
        id: _content

        anchors.fill: parent
        anchors.topMargin: Metrics.gapM

        // Visualizes all action sequences associated with this input.
        ScrollList {
            id: _listView

            Layout.fillHeight: true
            Layout.fillWidth: true

            visible: count > 0
            scrollbarAlwaysVisible: true
            spacing: Metrics.gapS

            model: _root.inputItemModel
            delegate: _entryDelegate
            reuseItems: false

            // Drop sequence above the first action sequence.
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

        // Action sequence instance visualization.
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

                    // Button to add a new action sequence below this one. Changes its
                    // visual appearance on hover, to turn from a plan text visual to
                    // a clear button visual.
                    Button {
                        id: _ghostRow

                        Layout.fillWidth: true
                        Layout.leftMargin: Metrics.gapM
                        Layout.rightMargin: Metrics.gapM * 2
                        implicitHeight: Metrics.rowAction

                        text: "New Action Sequence"
                        icon.name: "plus"

                        background: Item {
                            Rectangle {
                                visible: !(_ghostRow.hovered || _ghostRow.down)
                                anchors.verticalCenter: parent.verticalCenter
                                width: parent.width
                                height: Metrics.hairline
                                color: Theme.line
                            }

                            Rectangle {
                                visible: !(_ghostRow.hovered || _ghostRow.down)
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.horizontalCenter: parent.horizontalCenter
                                width: 200
                                height: Metrics.hairline
                                color: Theme.bg
                            }

                            Rectangle {
                                visible: _ghostRow.hovered || _ghostRow.down
                                anchors.fill: parent
                                color: "transparent"
                                radius: Metrics.radius
                                border.width: Metrics.hairline
                                border.color: Theme.line
                            }
                        }

                        onClicked: () => {
                            _root.inputItemModel.newActionSequence()
                        }
                    }
                }

                // Drop location below the action sequence for reordering of entire
                // action sequences via drag&drop.
                RowDropBand {
                    target: _ghostRow
                    coverTarget: true

                    validationCallback: function(drop) {
                        return drop.getDataAsString("type") === "sequence"
                    }
                    dropCallback: function(drop) {
                        _root.inputItemModel.dropAction(
                            drop.text,
                            modelData.rootAction.id,
                            false
                        )
                    }
                }
            }
        }

        // Button shown when no actions are mapped to this input to clearly guide the
        // user to the first step.
        Button {
            id: _emptyStateButton

            visible: _listView.count === 0
            Layout.fillWidth: true
            Layout.preferredHeight: Metrics.rowInput
            Layout.margins: Metrics.gapM

            text: "New Action Sequence"
            icon.name: "plus"

            onClicked: () => {
                _root.inputItemModel.newActionSequence()
            }
        }
    }
}
