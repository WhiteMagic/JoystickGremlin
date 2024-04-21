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

import QtQuick.Controls.Universal

import Gremlin.Profile


Window {
    id: _root

    minimumWidth: 900
    minimumHeight: 500

    title: "Manage Modes"

    property ModeHierarchyModel mode : backend.modeHierarchy
    property ModeListModel modeList : mode.modeList

    TextInputDialog {
        id: _textInput

        visible: false

        property var callback: null

        onAccepted: function(value)
        {
            callback(value)
            visible = false
        }
    }

    ColumnLayout {
        id: _content

        anchors.fill: parent

        ListView  {
            id: _blalist
            Layout.fillWidth: true
            Layout.fillHeight: true

            flickableDirection: Flickable.VerticalFlick
            boundsBehavior: Flickable.StopAtBounds
            spacing: 10

            model: mode.modeList

            delegate: _delegate
        }

        Button {
            Layout.alignment: Qt.AlignHCenter

            text: "Add Mode"

            onClicked: function()
            {
                let validNames = mode.modeStringList()

                _textInput.title = "Add new mode"
                _textInput.text = "New mode"
                _textInput.validator = function(value)
                {
                    return !validNames.includes(value)
                }
                _textInput.callback = function(name) {
                    mode.newMode(name)
                }
                _textInput.visible = true
            }
        }
    }

    Component {
        id: _delegate

        RowLayout {
            required property string name
            required property string parentName

            width: ListView.view.width
            height: _parentMode.height

            TextInput {
                Layout.fillWidth: true
                Layout.leftMargin: 10

                font.pixelSize: 15
                padding: 4

                text: name
            }

            IconButton {
                text: Constants.edit

                Layout.leftMargin: 10

                onClicked: function()
                {
                    let validNames = mode.validParents(name)

                    _textInput.text = name
                    _textInput.callback = function(value)
                    {
                        mode.renameMode(name, value)
                    }
                    _textInput.validator = function(value)
                    {
                        return !validNames.includes(value)
                    }
                    _textInput.visible = true
                }
            }

            ComboBox {
                id: _parentMode

                Layout.preferredWidth: 200
                Layout.leftMargin: 10
                Layout.rightMargin: 10

                model: mode.validParents(name)

                textRole: "value"
                valueRole: "value"

                onActivated: function(index)
                {
                    mode.setParent(name, currentValue)
                }

                Component.onCompleted: function()
                {
                    currentIndex = indexOfValue(parentName)
                }
            }

            IconButton {
                text: Constants.trash

                Layout.rightMargin: 10

                onClicked: function()
                {
                    mode.deleteMode(name)
                }
            }
        }
    }
}