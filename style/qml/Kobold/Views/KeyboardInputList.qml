// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Kobold.Foundation
import Kobold.Controls

// Visualizes the inputs and information about their associated actions
// contained in a Device instance.
Rectangle {
    color: Theme.bgAlt

    // List of all existing inputs.
    ColumnLayout {
        id: _content

        anchors.fill: parent

        ScrollList {
            id: _inputList

            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.leftMargin: Metrics.gapM
            Layout.topMargin: Metrics.gapM

            scrollbarAlwaysVisible: true
            spacing: Metrics.gapS
            reuseItems: true

            model: KeyboardManagerModel {}

            delegate: InputButton {
                id: _row

                width: _inputList.width - Metrics.gapM * 2
                height: Metrics.rowInput

                selected: index === _inputList.currentIndex
                onClicked: () => { _inputList.currentIndex = index }

                deleteButton: ToolButton {
                    icon.name: "delete"
                    padding: Metrics.gapS

                    // Lazily-instantiated (Loader-created) Components don't
                    // see the delegate's own required properties by bare
                    // name -- go through the id instead.
                    onClicked: () => { _inputList.model.deleteInput(_row.index) }
                }
            }

            footer: Item {
                width: ListView.view.width
                height: Metrics.gapM
            }

            onCurrentIndexChanged: () => {
                uiState.setCurrentInput(
                    model.inputIdentifier(currentIndex),
                    currentIndex
                )
            }
         }

        InputCaptureButton {
            Layout.margins: Metrics.gapL
            Layout.alignment: Qt.AlignBottom | Qt.AlignHCenter

            text: "Add Key"
            callback: (inputs) => { _inputList.model.addKey(inputs) }
            multipleInputs: false
            eventTypes: ["key"]
        }
    }
}
