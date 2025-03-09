// -*- coding: utf-8; -*-
//
// Copyright (C) 2022 Lionel Ott
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

import Gremlin.Config
import "helpers.js" as Helpers


Window {
    minimumWidth: 800
    minimumHeight: 600

    title: "Options"

    ConfigSectionModel {
        id: _sectionModel
    }

    RowLayout {
        id: _root

        anchors.fill: parent

        // Shows the list of all option sections
        ListView {
            id: _sectionSelector

            Layout.preferredWidth: 200
            Layout.fillHeight: true

            model: _sectionModel
            delegate: ConfigSectionButton {}

            Component.onCompleted: () => {
                itemAtIndex(0).toggle()
            }
        }

        // Shows the contents of the currently selected section
        ConfigSection {
            id: _configSection

            Layout.fillHeight: true
            Layout.fillWidth: true
        }
    }
}