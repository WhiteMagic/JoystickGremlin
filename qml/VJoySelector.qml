// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Device


Item {
    id: _root

    property int vjoyDeviceId
    property string vjoyInputType
    property int vjoyInputId
    property alias validTypes: _vjoy.validTypes

    signal selectionChanged(int deviceId, string inputType, int inputId)

    implicitHeight: _content.height
    implicitWidth: _content.implicitWidth

    // React to the validTypes value being changed from an external source.
    function initialize(vjoy_id, input_type, input_id) {
        _vjoy.setInitialState(vjoy_id, input_type, input_id)
    }

    VJoyDevices {
        id: _vjoy

        // Persist UI changes to the model.
        // onSelectionChanged: (vjoyId, inputType, inputId) => {
        //     // Order matters, updating input id first results in the type
        //     // possibly being uninitialized.
        //     _root.vjoyDeviceId = _vjoy.vjoyId
        //     _root.vjoyInputType = _vjoy.inputType
        //     _root.vjoyInputId = _vjoy.inputId
        // }
        // onVjoyIndexChanged: () => {
        //     _root.selectionChanged(_vjoy.vjoyId, _vjoy.inputType, _vjoy.inputId)
        // }
        //     //  _root.vjoyDeviceId =  }
        // onInputIndexChanged: () => {
        //     // Order matters, updating input id first results in the type
        //     // possibly being uninitialized.
        //     // _root.vjoyInputType = _vjoy.inputType
        //     // _root.vjoyInputId = _vjoy.inputId
        //     _root.selectionChanged(_vjoy.vjoyId, _vjoy.inputType, _vjoy.inputId)
        // }

        onCurrentSelectionChanged: (vjoy_id, input_type, input_id) => {
            console.log(vjoy_id + " " + input_type + " " + input_id)

            _device.currentIndex = _device.find("vJoy Device " + vjoy_id)
            _input.currentIndex = ""
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
            // currentIndex: _vjoy.vjoyIndex

            onActivated: (index) => { _vjoy.vjoyIndex = index }
        }

        BetterComboBox {
            id: _input

            Layout.minimumWidth: 150
            Layout.fillWidth: true

            model: _vjoy.inputChoices
            // currentIndex: _vjoy.inputIndex

            onActivated: (index) =>  { _vjoy.inputIndex = index }
        }

        HorizontalDivider {}

        Label {
            visible: !_vjoy.hasValidVJoyDevices

            text: "No vJoy devices available."
            color: Style.error
        }
    }
}
