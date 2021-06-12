// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2020 Lionel Ott
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.


import QtQuick 2.14
import QtQuick.Controls 2.14

import gremlin.ui.device 1.0


Item {
    id: _root

    property string vjoyInputType
    property int vjoyDeviceId
    property int vjoyInputId
    property var validTypes

    height: Math.max(_device.height, idSpacer.height, idInput.height)
    width: _device.width + idSpacer.width + idInput.width

    // React to the validTypes value being changed from an external source
    onValidTypesChanged: {
        _vjoy.validTypes = validTypes
    }


    VJoyDevices {
        id: _vjoy

        Component.onCompleted: {
            validTypes = _root.validTypes
            setSelection(
                _root.vjoyDeviceId,
                _root.vjoyInputId,
                _root.vjoyInputType
            )
        }

        onVjoyIndexChanged: {
            _root.vjoyDeviceId = _vjoy.vjoyId
        }
        onInputIndexChanged: {
            _root.vjoyInputId = _vjoy.inputId
            _root.vjoyInputType = _vjoy.vjoyInputType
        }
    }

    ComboBox {
        id: _device

        anchors.left: parent.left
        width: 150

        model: _vjoy.deviceModel
        currentIndex: _vjoy.vjoyIndex

        onActivated: {
            _vjoy.vjoyIndex = index;
        }
    }

    Rectangle {
        id: idSpacer
        anchors.left: _device.right
        width: 10
        height: 1

        color: "transparent"
    }

    ComboBox {
        id: idInput

        anchors.left: idSpacer.right
        width: 150

        model: _vjoy.inputModel
        currentIndex: _vjoy.inputIndex

        onActivated: {
            _vjoy.inputIndex = index
        }
    }
}