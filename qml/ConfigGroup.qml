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
import Qt.labs.qmlmodels

import Gremlin.Config
import "helpers.js" as Helpers


Item {
    property ConfigGroupModel groupModel

    ListView {
        id: _content

        implicitHeight: contentItem.childrenRect.height
        anchors.left: parent.left
        anchors.right: parent.right

        model: groupModel
        delegate: _groupComponent
    }

    Component {
        id: _groupComponent

        Item {
            required property int index
            required property string groupName
            required property ConfigEntryModel entryModel

            width: parent.width
            height: _groupItem.childrenRect.height

            Column {
                id: _groupItem

                anchors.left: parent.left
                anchors.right: parent.right

                // Group header
                RowLayout {
                    anchors.left: parent.left
                    anchors.right: parent.right

                    DisplayText {
                        text: Helpers.capitalize(groupName)

                        font.pointSize: 12
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignVCenter

                        height: 2
                        color: Universal.baseLowColor
                    }
                }

                // Group entries
                ListView {
                    implicitHeight: contentItem.childrenRect.height
                    anchors.left: parent.left
                    anchors.right: parent.right

                    model: entryModel
                    delegate: _entryDelegateChooser
                }
            }
        }
    }

    DelegateChooser {
        id: _entryDelegateChooser
        role: "data_type"

        property int controlWidth: 200

        DelegateChoice {
            roleValue: "bool"

            RowLayout {
                Switch {
                    Layout.preferredWidth: _entryDelegateChooser.controlWidth

                    checked: value

                    onToggled: function () {
                        value = checked
                    }
                }
                Label {
                    Layout.fillWidth: true

                    text: description
                }
            }
        }
        DelegateChoice {
            roleValue: "float"

            RowLayout {
                FloatSpinBox {
                    Layout.preferredWidth: _entryDelegateChooser.controlWidth

                    realValue: value
                    minValue: properties.min
                    maxValue: properties.max

                    onRealValueModified: function() {
                        value = realValue
                    }
                }
                Label {
                    Layout.fillWidth: true

                    text: description
                }
            }
        }
        DelegateChoice {
            roleValue: "int"

            RowLayout {
                SpinBox {
                    Layout.preferredWidth: _entryDelegateChooser.controlWidth

                    value: model.value
                    from: properties.min
                    to: properties.max

                    onValueModified: function() {
                        model.value = value
                    }
                }
                Label {
                    Layout.fillWidth: true

                    text: description
                }
            }
        }
        DelegateChoice {
            roleValue: "string"

            RowLayout {
                TextInput {
                    Layout.preferredWidth: _entryDelegateChooser.controlWidth

                    text: value

                    onTextEdited: function() {
                        value = text
                    }
                }

                Label {
                    Layout.fillWidth: true

                    text: description
                }
            }
        }
        DelegateChoice {
            roleValue: "selection"
            
            RowLayout {
                ComboBox {
                    Layout.preferredWidth: _entryDelegateChooser.controlWidth

                    model: properties.valid_options

                    Component.onCompleted: function() {
                        currentIndex = find(value)
                    }

                    onActivated: function(index) {
                        value = currentValue
                    }

                }

                Label {
                    Layout.fillWidth: true

                    text: description
                }
            }
        }
    }
}