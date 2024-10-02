// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2024 Lionel Ott
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

import QtQuick.Controls.Universal

import Gremlin.Profile
import Gremlin.ActionPlugins
import "../../qml"


Item {
    id: _root

    property PauseResumeModel action

    implicitHeight: _content.height

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        RadioButton {
            text: "Pause"

            checked: _root.action.operation === "Pause"
            onClicked: function() {
                _root.action.operation = "Pause"
            }
        }
        RadioButton {
            text: "Resume"

            checked: _root.action.operation === "Resume"
            onClicked: function() {
                _root.action.operation = "Resume"
            }
        }
        RadioButton {
            text: "Toggle"

            checked: _root.action.operation === "Toggle"
            onClicked: function() {
                _root.action.operation = "Toggle"
            }
        }
    }
}