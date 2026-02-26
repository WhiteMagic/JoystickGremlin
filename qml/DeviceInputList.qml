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
    id: _root

    property Device device
    property int minimumWidth: _inputList.minimumWidth

    // Sychronize input selection when the underlying device changes.
    Connections {
        target: uiState

        function onDeviceChanged() {
            // Forcibly refresh the selected input.
            let tmp = uiState.currentInputIndex
            _inputList.currentIndex = -1
            _inputList.currentIndex = tmp
        }
    }

    Connections {
        target: signal

        function onSetInputIndex(index) {
            _inputList.currentIndex = index
        }
    }

    // List of all the inputs available on the device
    JGListView {
        id: _inputList
        anchors.fill: parent
        scrollbarAlwaysVisible: true

        property int minimumWidth: 250

        model: device
        delegate: _deviceDelegate

        onCurrentIndexChanged: () => {
            uiState.setCurrentInput(
                device.inputIdentifier(currentIndex),
                currentIndex
            )
        }
    }

    // Renders the information about a single input, including name and
    // overview of the associated actions.
    Component {
        id: _deviceDelegate

        Rectangle {
            id: _inputDisplay

            width: _inputList.width
            implicitWidth: _inputLabel.width + _inputOverview.width + 50
            height: 50

            // Dynamically compute the minimum width required to fully display
            // the input information. This is used to properly configure the
            // SplitView component.
            Component.onCompleted: {
                _inputList.minimumWidth = Math.max(
                    _inputList.minimumWidth,
                    implicitWidth
                )
            }

            color: model.index === _inputList.currentIndex
                ? Universal.chromeMediumColor : Style.background

            MouseArea {
                anchors.fill: parent
                onClicked: () => { _inputList.currentIndex = model.index }
            }

            Label {
                id: _inputLabel
                text: name
                font.weight: 600

                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.leftMargin: 5
                anchors.topMargin: 5
            }

            // Label {
            //     id: _inputOverview
            //     text: actionSequenceInfo

            //     horizontalAlignment: Text.AlignRight
            //     verticalAlignment: Text.AlignVCenter

            //     anchors.top: parent.top
            //     anchors.right: _inputDisplay.right
            //     anchors.rightMargin: 20
            //     anchors.topMargin: 5
            // }
            Image {
                id: _inputOverview
                source: "image://action_summary/" + actionSequenceDescriptor
                asynchronous: true
                cache: false
                width: sourceSize.width
                height: sourceSize.height

                anchors.top: parent.top
                anchors.right: _inputDisplay.right
                anchors.rightMargin: 20
                anchors.topMargin: 5
            }

            JGText {
                id: _inputDescription
                text: description
                font.italic: true

                width: parent.width - 30
                elide: Text.ElideRight

                anchors.left: parent.left
                anchors.bottom: parent.bottom
                anchors.leftMargin: 5
                anchors.bottomMargin: 5
            }
        }
    }
}
