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

    height: idDevice.height

    onValidTypesChanged: {
        idVjoy.validTypes = validTypes
    }

    VJoyDevices {
        id: idVjoy
        validTypes: validTypes
    }

    Rectangle {
        Row {
            anchors.left: parent.left
            anchors.right: parent.right

            ComboBox {
                id: idDevice

                model: idVjoy.deviceModel
                currentIndex: vjoyDeviceId

                onCurrentIndexChanged: {
                    idVjoy.selectVjoyDevice(currentIndex)
                    vjoyDeviceId = currentIndex
                }
            }
            ComboBox {
                id: idInput

                model: idVjoy.inputModel
                currentIndex: vjoyInputId

                onCurrentIndexChanged: {
                    vjoyInputId = currentIndex
                }

            }
        }
    }
}