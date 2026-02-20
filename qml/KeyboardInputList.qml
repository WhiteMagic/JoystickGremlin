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

            Layout.minimumWidth: 250
            Layout.fillHeight: true
            Layout.fillWidth: true
            scrollbarAlwaysVisible: true

            model: KeyboardManagerModel {}
            delegate: _entryDelegate

            onCurrentIndexChanged: () => {
                console.log("Selected input index: " + currentIndex)
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


    Component {
        id: _entryDelegate

        Item {
            id: _delegate

            height: _inputDisplay.height
            width: _inputDisplay.width

            required property int index
            required property string name
            required property int actionCount
            property ListView view: ListView.view
            property KeyboardManagerModel model: view.model

            // Renders the entire "button" area of the singular input.
            Rectangle {
                id: _inputDisplay

                implicitWidth: view.width - _inputList.ScrollBar.vertical.width
                height: 50

                color: index == view.currentIndex
                    ? Universal.chromeMediumColor : Universal.background

                MouseArea {
                    anchors.fill: parent
                    onClicked: () => { view.currentIndex = index }
                }

                // User specified name assigned to this output.
                Label {
                    text: name
                    font.weight: 600

                    anchors.top: parent.top
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.leftMargin: 5
                    anchors.topMargin: 5
                }

                Label {
                    text: actionCount ? actionCount : ""

                    anchors.top: parent.top
                    anchors.right: _btnTrash.left
                    anchors.rightMargin: 5
                    anchors.topMargin: 5
                }

                // Button to remove an input
                IconButton {
                    id: _btnTrash
                    text: bsi.icons.remove
                    font.pixelSize: 12

                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.rightMargin: 5
                    anchors.topMargin: 5

                    onClicked: () => { model.deleteInput(name) }
                }

            }
        }
    }

}