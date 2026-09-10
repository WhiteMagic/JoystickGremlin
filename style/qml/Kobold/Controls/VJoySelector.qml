// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Device
import Kobold.Foundation

// UI item used to select a vJoy input, this is intended to be used everywhere a vJoy
// input needs to be selected.
Item {
    id: root

    property alias validTypes: _vjoy.validTypes

    signal selectionChanged(int deviceId, string inputType, int inputId)

    implicitHeight: _content.implicitHeight
    implicitWidth: _content.implicitWidth

    function initialize(vjoyId, inputType, inputId) {
        _vjoy.setInitialState(vjoyId, inputType, inputId)
    }

    function updateState() {
        _vjoy.setState(_deviceCombo.currentText, _inputCombo.currentText)
    }

    VJoyDevices {
        id: _vjoy

        onCurrentSelectionChanged: (vjoyId, inputType, inputId) => {
            root.selectionChanged(vjoyId, inputType, inputId)
        }

        onCurrentValuesChanged: (vjoyName, inputName) => {
            _deviceCombo.currentIndex = _deviceCombo.find(vjoyName)
            _inputCombo.currentIndex = _inputCombo.find(inputName)
        }
    }

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: Metrics.gapM

        ComboBox {
            id: _deviceCombo

            model: _vjoy.vjoyDevices

            onActivated: root.updateState()
        }

        ComboBox {
            id: _inputCombo

            model: _vjoy.inputChoices

            onActivated: root.updateState()
        }

        Label {
            visible: !_vjoy.hasValidVJoyDevices
            text: "No vJoy devices available."
            color: Theme.error
        }
    }
}
