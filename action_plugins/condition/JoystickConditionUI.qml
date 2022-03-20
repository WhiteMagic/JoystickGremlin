// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2022 Lionel Ott
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
import QtQuick.Window

import Gremlin.ActionPlugins
import Gremlin.Util

import "../../qml"


Item {
    id: _root

    function formatInputs(data)
    {
        var text = "<ul>";
        data.forEach(function(entry) {
            text += "<li>" + entry + "</li>";
        })
        text += "</ul>";
        return text;
    }

    property JoystickCondition model
    property string conditionText: formatInputs(model.inputs)
    
    // Format the condition inputs as an unordered list
    Connections {
        target: model
        function onInputsChanged(data)
        {
            _root.conditionText = formatInputs(data);
        }
    }

    implicitHeight: _content.height

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right
        
        Layout.fillWidth: true

        Label {
            text: "Joystick Condition" + _root.conditionText
        }

        InputListener {
            Layout.alignment: Qt.AlignRight | Qt.AlignTop

            callback: _root.model.updateInputs
            multipleInputs: true
            eventTypes: ["button"]
        }
    }
}