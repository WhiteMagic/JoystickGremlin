// -*- coding: utf-8; -*-
//
// Copyright (C) 2025 Lionel Ott
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
import QtQuick.Dialogs
import QtQuick.Layouts
import Qt.labs.qmlmodels

import Gremlin.Plugin

import "helpers.js" as Helpers


Item {
    id: _root

    property ScriptListModel scriptListModel : backend.scriptListModel

    // Dialog to select a script to add
    FileDialog {
        id: _selectScript

        title: "Please select a file"

        acceptLabel: "Load"
        defaultSuffix: "py"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Script files (*.py)"]

        onAccepted: function()
        {
            scriptListModel.addScript(Helpers.pythonizePath(selectedFile))
        }
    }

    // Dialog to rename a script
    TextInputDialog {
        id: _renameScriptDialog

        visible: false
        width: 300

        property var callback: null

        onAccepted: function(value)
        {
            callback(value)
            visible = false
        }
    }

    SplitView {
        anchors.fill: parent
        anchors.leftMargin: 10

        ColumnLayout {
            SplitView.fillHeight: true
            SplitView.fillWidth: true

            ListView {
                id: _view
                model: scriptListModel

                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.rightMargin: 5

                spacing: 10

                // Make it behave like a sensible scrolling container
                ScrollBar.vertical: ScrollBar {
                    policy: ScrollBar.AlwaysOn
                }
                flickableDirection: Flickable.VerticalFlick
                boundsBehavior: Flickable.StopAtBounds

                delegate: ScriptUI {
                    Layout.margins: 10
                    width: _view.width
                }
            }

            Button {
                Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom
                Layout.preferredHeight: 30
                Layout.bottomMargin: 10

                text: "Add Script"

                onClicked: () => _selectScript.open()
            }
        }

        ScriptConfiguration {
            id: _config

            SplitView.fillHeight: true
            SplitView.minimumWidth: 500
        }
    }

    component ScriptUI : RowLayout {
        id: _item

        required property string path
        required property string name
        required property var variables

        Text {
            Layout.leftMargin: 10
            text: bsi.icons.script
            font.pixelSize: 18
        }

        Text {
            id: _path

            Layout.alignment: Qt.AlignVCenter

            text: _item.path
            leftPadding: 10
        }

        LayoutHorizontalSpacer {}

        Text {
            id: _name

            Layout.preferredWidth: 200
            Layout.alignment: Qt.AlignVCenter

            text: _item.name
            rightPadding: 50
        }

        IconButton {
            text: bsi.icons.edit

            onClicked: {
                _renameScriptDialog.text = name
                _renameScriptDialog.callback = (value) => {
                    scriptListModel.renameScript(path, name, value)
                }
                _renameScriptDialog.visible = true
            }
        }

        IconButton {
            text: bsi.icons.configure

            onClicked: {
                _config.model = variables
            }
        }

        IconButton {
            Layout.rightMargin: 20
            text: bsi.icons.trash

            onClicked: () => scriptListModel.removeScript(path, name)
        }
    }
}