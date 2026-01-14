// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Gremlin.Profile
import Gremlin.Style

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

        // Show all actions associated with this input
        JGListView {
            id: _listView

            Layout.fillHeight: true
            Layout.fillWidth: true
            scrollbarAlwaysVisible: true

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

        // Button to add a new action configuration to the currently
        // active input
        Rectangle {
            id: _newActionButton

            Layout.fillWidth: true
            Layout.preferredHeight: 40

            color: Style.background

            Button {
                anchors.horizontalCenter: parent.horizontalCenter

                text: "New Action Sequence"

                onClicked: {
                    _root.inputItemModel.newActionSequence()
                }
            }
        }
    }
}
