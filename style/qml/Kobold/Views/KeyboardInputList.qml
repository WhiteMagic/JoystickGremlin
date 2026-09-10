// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Kobold.Controls
import Kobold.Foundation

// Visualizes the inputs configured for keyboard keys.
Rectangle {
    color: Theme.bgAlt

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
            Layout.fillWidth: true
            Layout.margins: Metrics.gapL

            text: "Add Key"

            variant: "bordered"
            fillColor: Theme.bg

            callback: (inputs) => { _inputList.model.addKey(inputs) }
            multipleInputs: false
            eventTypes: ["key"]
        }
    }
}
