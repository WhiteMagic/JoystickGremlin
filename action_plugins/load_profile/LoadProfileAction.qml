// -*- coding: utf-8; -*-
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
import QtQuick.Dialogs

import QtQuick.Controls.Universal

import Gremlin.Profile
import Gremlin.ActionPlugins
import "../../qml"


Item {
    property LoadProfileModel action

    implicitHeight: _content.height

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        Label {
            id: _label

            Layout.preferredWidth: 150

            text: "Profile filename"
        }

        TextField {
            id: _profile_filename

            Layout.fillWidth: true

            placeholderText: null != action ? null : "Enter a profile filename"
            text: action.profile_filename
            selectByMouse: true

            onTextChanged: {
                action.profile_filename = text
            }
        }

        Button {
            text: "Select File"
            onClicked: fileDialog.open()
        }

   }

   FileDialog {
        id: fileDialog
        title: "Select a File"
        onAccepted: {
            _profile_filename.text = new URL(selectedFile).pathname.substring(1)
        }
    }
}
