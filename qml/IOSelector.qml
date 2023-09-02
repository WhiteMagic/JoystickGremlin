// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2023 Lionel Ott
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

    property string ioInputType
    // property string ioInputGuid

    property alias ioInputGuid: _model.currentGuid
    property alias validTypes: _model.validTypes

    implicitHeight: _content.height
    implicitWidth: _content.implicitWidth


    IODeviceInputsModel {
        id: _model
    }

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 10

        ComboBox {
            Layout.minimumWidth: 250
            Layout.fillWidth: true

            model: _model
            textRole: "label"
            currentIndex: _model.currentSelectionIndex
            delegate: OptionDelegate {}
        }
    }

    component OptionDelegate : ItemDelegate {
        required property string label
        required property string guid

        width: parent.width
        text: label

        onClicked: function()
        {
            _model.currentGuid = guid
        }
    }

}