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
        anchors.leftMargin: 10

        scrollbarAlwaysVisible: true
        spacing: 5

        model: device
        delegate: InputButton {
            width: _inputList.width - 20
            height: 50

            selected: model.index === _inputList.currentIndex
            onClicked: () => { _inputList.currentIndex = model.index }
        }

        Component.onCompleted: () => {
            uiState.setCurrentInput(
                device.inputIdentifier(currentIndex),
                currentIndex
            )
        }

        onCurrentIndexChanged: () => {
            uiState.setCurrentInput(
                device.inputIdentifier(currentIndex),
                currentIndex
            )
        }
    }
}
