// -*- coding: utf-8; -*-
//
// Copyright (C) 2020 Lionel Ott
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

    // React to the validTypes value being changed from an external source
    onValidTypesChanged: () => {
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

            onActivated: function(index)
            {
                _vjoy.vjoyIndex = index;
            }
        }

        BetterComboBox {
            id: _input

            Layout.minimumWidth: 150
            Layout.fillWidth: true

            model: _vjoy.inputModel
            currentIndex: _vjoy.inputIndex

            onActivated: function(index)
            {
                _vjoy.inputIndex = index
            }
        }
    }
}