// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Gremlin.Profile

import Kobold.Foundation

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

        // Show all actions associated with this input. SPEC §8: sequences are independent
        // trees, separated by 8px of space -- never a rule between them (each sequence
        // provides its own 8px padding, see qml/InputItemBinding.qml).
        JGListView {
            id: _listView

            Layout.fillHeight: true
            Layout.fillWidth: true
            scrollbarAlwaysVisible: true
            spacing: Metrics.gapM
            // Delegates here are whole action-sequence trees, not short uniform rows --
            // step-scroll can't reach content past the first index (see JGListView.qml).
            stepScroll: false

            // Content to visualize
            model: _root.inputItemModel
            delegate: _entryDelegate
        }

        // ListView delegate definition rendering individual bindings
        // via ActionTree instances
        Component {
            id: _entryDelegate

            Item {
                id: _delegate

                height: _binding.height
                width: _binding.width

                required property int index
                required property var modelData
                property ListView view: ListView.view

                InputItemBinding {
                    id: _binding

                    // Have to set the width here as Layout fields don't exist
                    // and we have to fill the view itself which will resize
                    // based on the layout
                    implicitWidth: view.width

                    inputBinding: modelData
                    inputItemModel: _root.inputItemModel
                }
            }
        }

        // Button to add a new action configuration to the currently active input. SPEC §8:
        // "New action sequence" is an ordinary push button -- not filled.
        Button {
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: Metrics.gapM

            text: "New Action Sequence"

            onClicked: {
                _root.inputItemModel.newActionSequence()
            }
        }
    }
}
