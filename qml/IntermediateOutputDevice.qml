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

import Gremlin.Device


// Visualizes the inputs and information about their associated actions
// contained in the IntermediateOutput system.
Item {
    id: _root

    property IODevice device
    property int inputIndex
    property InputIdentifier inputIdentifier

    // List of all the inputs configured
    ColumnLayout {
        id: _content

        anchors.fill: parent

        ListView {
            id: _inputList

            Layout.minimumWidth: 100
            Layout.fillHeight: true
            Layout.fillWidth: true

            model: device
            delegate: _entryDelegate

            onCurrentIndexChanged: {
                inputIndex = currentIndex
                inputIdentifier = device.inputIdentifier(currentIndex)
            }

            // Make it behave like a sensible scrolling container
            ScrollBar.vertical: ScrollBar {}
            flickableDirection: Flickable.VerticalFlick
            boundsBehavior: Flickable.StopAtBounds
        }

        // Controls to add new intermediate output instances
        RowLayout {
            Layout.minimumWidth: 100
            Layout.preferredHeight: 50

            ComboBox {
                id: _input_type

                Layout.fillWidth: true

                model: ["Axis", "Button", "Hat"]
            }

            IconButton {
                text: Constants.add
                backgroundColor: Universal.baseLowColor

                onClicked: function()
                {
                    device.createInput(_input_type.currentValue)
                }
            }
        }
    }

    Component {
        id: _entryDelegate

        Item {
            id: _delegate

            height: _inputDisplay.height
            width: _inputDisplay.width

            required property int index
            required property string name
            required property string label
            required property int actionCount
            property ListView view: ListView.view

            property bool isEditing: false
            property string old_name

            // Renders the entire "button" area of the singular input
            Rectangle {
                id: _inputDisplay

                implicitWidth: view.width
                height: 50

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        view.currentIndex = index
                    }
                }

                color: index == view.currentIndex
                    ? Universal.chromeMediumColor : Universal.background

                Text {
                    text: name

                    padding: 4
                    anchors.left: parent.left
                    anchors.bottom: parent.bottom
                }

                Text {
                    text: actionCount

                    padding: 4
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                }

                // Editable label of the input which also allows for selecting
                // the input.
                TextInput {
                    id: _label

                    text: label
                    font.pixelSize: 15
                    padding: 4

                    activeFocusOnPress: false
                    readOnly: !isEditing
                    selectByMouse: isEditing

                    anchors.left: parent.left
                    anchors.right: _btnEdit.left

                    cursorVisible: isEditing
                    z: 3

                    onActiveFocusChanged: function()
                    {
                        if(activeFocus)
                        {
                            old_name = text
                            view.currentIndex = index
                        }
                    }

                    onEditingFinished: function()
                    {
                        isEditing = false
                        device.changeName(old_name, text)
                        old_name = text
                    }
                }

                // Outline for the TextEdit field
                Rectangle {
                    anchors.fill: _label
                    visible: isEditing

                    color: parent.color
                    border {
                        color: Universal.accent
                        width: 1
                    }
                    z: 2
                }

                // Button to remove an input
                IconButton {
                    id: _btnTrash
                    text: Constants.trash

                    topPadding: 4
                    padding: 4
                    anchors.right: parent.right
                    anchors.top: parent.top

                    onClicked: function()
                    {
                        device.deleteInput(_label.text)
                    }
                }

                // Button enabling the editing of the input's label
                IconButton {
                    id: _btnEdit
                    text: Constants.edit

                    topPadding: 4
                    padding: 4
                    anchors.right: _btnTrash.left
                    anchors.top: parent.top

                    onClicked: function()
                    {
                        isEditing = true
                        _label.focus = true
                    }
                }
            }
        }
    }
}