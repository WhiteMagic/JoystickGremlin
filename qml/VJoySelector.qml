// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Device


Item {
    id: _root

    property alias validTypes: _vjoy.validTypes

    signal selectionChanged(int deviceId, string inputType, int inputId)

    implicitHeight: _content.height
    implicitWidth: _content.implicitWidth

    // React to the validTypes value being changed from an external source.
    function initialize(vjoy_id, input_type, input_id) {
        _vjoy.setInitialState(vjoy_id, input_type, input_id)
    }

    function updateState() {
        _vjoy.setState(_device.currentText, _input.currentText)
    }

    VJoyDevices {
        id: _vjoy

        onCurrentSelectionChanged: (vjoyId, inputType, inputId) => {
            _root.selectionChanged(vjoyId, inputType, inputId)
        }

        onCurrentValuesChanged: (vjoy_name, input_name) => {
            _device.currentIndex = _device.find(vjoy_name)
            _input.currentIndex = _input.find(input_name)
        }
    }

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 10

        ComboBox {
            id: _device

            Layout.minimumWidth: 150
            Layout.fillWidth: true

            model: _vjoy.vjoyDevices

            onActivated: (index) => { updateState() }
        }

        BetterComboBox {
            id: _input

            Layout.minimumWidth: 150
            Layout.fillWidth: true

            model: _vjoy.inputChoices

            onActivated: (index) =>  { updateState() }
        }

        HorizontalDivider {}

        Label {
            visible: !_vjoy.hasValidVJoyDevices

            text: "No vJoy devices available."
            color: Style.error
        }
    }
}
