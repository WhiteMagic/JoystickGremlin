// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Kobold.Controls
import Kobold.Foundation

// Visualizes a device's inputs and information about actions associated with them.
// Rendered in the left panel of the main UI.
Rectangle {
    id: _root

    color: Theme.bgAlt

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

    // List of all the inputs available on the device.
    ScrollList {
        id: _inputList

        anchors.fill: parent
        anchors.leftMargin: Metrics.gapM
        anchors.topMargin: Metrics.gapM

        scrollbarAlwaysVisible: true
        spacing: Metrics.gapS
        reuseItems: true

        model: device

        delegate: InputButton {
            width: _inputList.width - Metrics.gapM * 2
            height: Metrics.rowInput

            selected: index === _inputList.currentIndex
            onClicked: { _inputList.currentIndex = index }
        }

        footer: Item {
            width: ListView.view.width
            height: Metrics.gapM
        }

        Component.onCompleted: {
            uiState.setCurrentInput(
                device.inputIdentifier(currentIndex),
                currentIndex
            )
        }

        onCurrentIndexChanged: {
            uiState.setCurrentInput(
                device.inputIdentifier(currentIndex),
                currentIndex
            )
        }
    }
}
