// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2019 Lionel Ott
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
    id: idRoot

    property string inputType
    property int vjoyDeviceId
    property int vjoyInputId
    property var validTypes

    height: Math.max(idDevice.height, idSpacer.height, idInput.height)
    width: idDevice.width + idSpacer.width + idInput.width

    // React to the validTypes value being changed from an external source
    onValidTypesChanged: {
        idVjoy.validTypes = validTypes
    }


    VJoyDevices {
        id: idVjoy

        Component.onCompleted: {
            validTypes = idRoot.validTypes
            setSelection(
                idRoot.vjoyDeviceId,
                idRoot.vjoyInputId,
                idRoot.inputType
            )
        }

        onVjoyIndexChanged: {
            idRoot.vjoyDeviceId = idVjoy.vjoyId
        }
        onInputIndexChanged: {
            idRoot.vjoyInputId = idVjoy.inputId
            idRoot.inputType = idVjoy.inputType
        }
    }

    ComboBox {
        id: idDevice

        anchors.left: parent.left
        width: 150

        model: idVjoy.deviceModel
        currentIndex: idVjoy.vjoyIndex

        onActivated: {
            idVjoy.vjoyIndex = index
        }
    }

    Rectangle {
        id: idSpacer
        anchors.left: idDevice.right
        width: 10
        height: 1
    }

    ComboBox {
        id: idInput

        anchors.left: idSpacer.right
        width: 150

        model: idVjoy.inputModel
        currentIndex: idVjoy.inputIndex

        onActivated: {
            idVjoy.inputIndex = index
        }
    }
}