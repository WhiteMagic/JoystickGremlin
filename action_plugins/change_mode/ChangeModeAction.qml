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

    property ChangeModeModel action
    property ModeHierarchyModel modes : backend.modeHierarchy

    implicitHeight: _content.height

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right


        ComboBox {
            id: _changeType
            model: ["Switch to", "Previous", "Unwind", "Cycle", "Temporary"]
        }

        Loader {
            active: _changeType.currentText === "Switch to"
            sourceComponent: _changeSwitchTo
        }

        Loader {
            active: _changeType.currentText === "Cycle"
            sourceComponent: _changeCycle
        }
    }

    // UI Components for the different change types

    Component {
        id: _changeSwitchTo

        RowLayout {
            Layout.fillWidth: true

            ComboBox {
                Layout.fillWidth: true
                model: _root.modes.modeList
                textRole: "name"
            }
        }
    }

    Component {
        id: _changeCycle

        RowLayout {
            Layout.fillWidth: true

            Text {
                text: "Cycle"
            }
        }
    }
}