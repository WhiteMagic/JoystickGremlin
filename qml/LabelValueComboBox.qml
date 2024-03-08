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
import QtQuick.Window

import QtQuick.Controls.Universal

import Gremlin.Profile


Item {
    id: _root

    property LabelValueSelectionModel model
    property alias value: _selection.currentValue
    signal selectionChanged()

    implicitHeight: _content.height
    implicitWidth: _content.implicitWidth

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 10

        ComboBox {
            id: _selection

            Layout.minimumWidth: 250
            Layout.fillWidth: true

            model: _root.model
            textRole: "label"
            currentIndex: model ? model.currentSelectionIndex : 0
            delegate: OptionDelegate {}
        }
    }

    // Delegate rendering the selection item using its label but using the
    // associated value for storage
    component OptionDelegate : ItemDelegate {
        required property string label
        required property string value
        required property string bootstrap
        required property string imageIcon

        width: parent.width
        contentItem: Row {
             Label {
                 text: bootstrap

                 width: bootstrap.length > 0 ? 30 : 0
                 verticalAlignment: Text.AlignBottom

                 font.family: "bootstrap-icons"
                 font.pixelSize: 20
             }
             Label {
                text: label
             }
        }

        onClicked: function()
        {
            _root.model.currentValue = value
            selectionChanged()
        }
    }

}

