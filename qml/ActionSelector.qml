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


import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts

import Gremlin.Profile


Item {
    id: _root

    property ActionNodeModel actionNode
    property var callback: null

    implicitHeight: _content.height
    implicitWidth: _button.width + _combobox.width + 13

    onActionNodeChanged: {
        _combobox.model = backend.actionList(actionNode)
    }

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        Button {
            id: _button

            Layout.leftMargin: 8
            text: "Add Action"

            onClicked: {
                _root.callback(_combobox.currentText)
            }
        }

        ComboBox {
            id: _combobox

            implicitContentWidthPolicy: ComboBox.WidestText
        }
    }
}