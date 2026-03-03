// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Gremlin.Style

// Visualizes the inputs and information about their associated actions
// contained in a Device instance.
Item {
    // List of all existing inputs.
    ColumnLayout {
        id: _content

        anchors.fill: parent

        JGListView {
            id: _inputList

            Layout.fillHeight: true
            Layout.fillWidth: true
            Layout.leftMargin: 10

            scrollbarAlwaysVisible: true
            spacing: 5

            model: KeyboardManagerModel {}
            delegate: InputButton {
                width: _inputList.width - 20
                height: 50

                selected: model.index === _inputList.currentIndex
                onClicked: () => { _inputList.currentIndex = model.index }

                deleteButton: IconButton {
                    text: bsi.icons.remove
                    font.pixelSize: 12
                    width: 15

                    onClicked: () => { _inputList.model.deleteInput(model.index) }
                }
            }

            onCurrentIndexChanged: () => {
                uiState.setCurrentInput(
                    model.inputIdentifier(currentIndex),
                    currentIndex
                )
            }
         }

        InputListener {
            Layout.margins: 10
            Layout.alignment: Qt.AlignBottom | Qt.AlignHCenter
            buttonWidth: parent.width - 20

            buttonLabel: "Add Key"
            callback: (inputs) => { _inputList.model.addKey(inputs) }
            multipleInputs: false
            eventTypes: ["key"]
        }
    }
}
