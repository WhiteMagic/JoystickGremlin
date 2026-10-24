// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Device
import Gremlin.UI
import Kobold.Foundation

// UI item used to select a vJoy input, this is intended to be used everywhere a vJoy
// input needs to be selected.
Item {
    id: root

    property var validTypes: []

    readonly property VJoyDevices _vjoy: ModelFactory.vjoyDevices(root)

    signal selectionChanged(int deviceId, string inputType, int inputId)

    implicitHeight: _content.implicitHeight
    implicitWidth: _content.implicitWidth

    onValidTypesChanged: () => { if (_vjoy) _vjoy.validTypes = validTypes }

    function initialize(vjoyId, inputType, inputId) {
        _vjoy.validTypes = validTypes
        _vjoy.setInitialState(vjoyId, inputType, inputId)
    }

    function updateState() {
        _vjoy.setState(_deviceCombo.currentText, _inputCombo.currentText)
    }

    Connections {
        target: root._vjoy

        function onCurrentSelectionChanged(vjoyId, inputType, inputId) {
            root.selectionChanged(vjoyId, inputType, inputId)
        }

        function onCurrentValuesChanged(vjoyName, inputName) {
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

            model: root._vjoy.vjoyDevices

            onActivated: root.updateState()
        }

        ComboBox {
            id: _inputCombo

            model: root._vjoy.inputChoices

            onActivated: root.updateState()
        }

        Label {
            visible: !root._vjoy.hasValidVJoyDevices
            text: "No vJoy devices available."
            color: Theme.error
        }
    }
}
