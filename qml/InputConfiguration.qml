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
import QtQuick.Layouts 1.14
import QtQuick.Window 2.14

import QtQuick.Controls.Universal 2.14

import gremlin.ui.profile 1.0


Item {
    id: root

    property ProfileModel profileModel

//        ActionList {
//            id: actionPanel
//
//            Layout.fillWidth: true
//        }

    ScrollView {
        anchors.fill: parent

        // Logic along the lines of:
        // Foreach library_item in input_item.actions do
        //     Render library_item

        ColumnLayout {

            anchors.fill: parent

            Repeater {
                // Model has to be the library item list thing
                model: 10

                // For now this will have to render each action, later on
                // this will need to be a special tree representation type
                DisplayText {
                    text: backend.help
                }
            }
        }
    }
}