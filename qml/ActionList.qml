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
import QtQuick.Layouts 1.14
import QtQuick.Window 2.14

import QtQuick.Controls.Universal 2.14

import gremlin.ui.profile 1.0


Item {
    id: idRoot

    property ProfileModel profileModel
//    property InputConfiguration inputConfiguration

//    ColumnLayout {

    RowLayout {
        anchors.fill: parent

        DisplayText {
            text: "Action"
            width: 300
        }
        ComboBox {
//                width: 200
            id: idActionLlist
            model: backend.action_list
//            font.pointSize: 10

//            menu.style.font.pointSize: 36
        }
        Button {
            text: "Add"
            font.pointSize: 10
            //onClicked: backend.add_action(
            //    inputConfiguration
            //    action_list.currentText
            //)
        }
    }

//    }
}