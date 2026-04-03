// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Device


Item {
    id: _root

    property string vjoyInputType
    property int vjoyDeviceId
    property int vjoyInputId
    property var validTypes

    implicitHeight: _content.height
    implicitWidth: _content.implicitWidth

    // React to the validTypes value being changed from an external source.
    onValidTypesChanged: () => { _vjoy.validTypes = validTypes }

    VJoyDevices {
        id: _vjoy

        Component.onCompleted: () => {
            validTypes = _root.validTypes
            setInitialState(
                _root.vjoyDeviceId,
                _root.vjoyInputId,
                _root.vjoyInputType
            )
        }

        onVjoyIndexChanged: () => { _root.vjoyDeviceId = _vjoy.vjoyId }
        onInputIndexChanged: () => {
            _root.vjoyInputId = _vjoy.inputId
            _root.vjoyInputType = _vjoy.inputType
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

            model: _vjoy.deviceModel
            currentIndex: _vjoy.vjoyIndex

            onActivated: (index) => { _vjoy.vjoyIndex = index }
        }

        BetterComboBox {
            id: _input

            Layout.minimumWidth: 150
            Layout.fillWidth: true

            model: _vjoy.inputModel
            currentIndex: _vjoy.inputIndex

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
