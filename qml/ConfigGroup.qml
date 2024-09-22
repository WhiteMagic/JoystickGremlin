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

    implicitHeight: _content.height

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        Repeater {
            id: _groupView

            Layout.fillWidth: true

            model: groupModel
            delegate: _groupDelegate
        }
    }

    Component {
        id: _groupDelegate

        Item {
            required property int index
            required property string groupName
            required property ConfigEntryModel entryModel

            implicitHeight: _groupItem.height

            ColumnLayout {
                id: _groupItem

                anchors.left: parent.left
                anchors.right: parent.right

                RowLayout {
                    Layout.fillWidth: true

                    DisplayText {
                        text: Helpers.capitalize(groupName)
                    }

                    Rectangle {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignVCenter

                        height: 2
                        color: Universal.baseLowColor
                    }
                }

                Repeater {
                    id: _entryView

                    model: entryModel
                    delegate: _entryDelegateChooser
                }
            }
        }
    }

    DelegateChooser {
        id: _entryDelegateChooser
        role: "data_type"

        DelegateChoice {
            roleValue: "bool"

            RowLayout {
                Switch {
                    Layout.preferredWidth: 150

                    checked: model.value

                    onToggled: function() {
                        model.value = checked
                    }
                }
                Label {
                    Layout.fillWidth: true

                    text: model.description
                }
            }
        }
        DelegateChoice {
            roleValue: "float"

            RowLayout {
                FloatSpinBox {
                    Layout.preferredWidth: 150

                    realValue: model.value
                    minValue: model.properties.min
                    maxValue: model.properties.max

                    onRealValueModified: function() {
                        model.value = realValue
                    }
                }
                Label {
                    Layout.fillWidth: true

                    text: model.description
                }
            }
        }
        DelegateChoice {
            roleValue: "int"

            RowLayout {
                SpinBox {
                    Layout.preferredWidth: 150

                    value: model.value
                    from: model.properties.min
                    to: model.properties.max

                    onValueModified: function() {
                        console.log(model.properties)
                        model.value = value
                    }
                }
                Label {
                    Layout.fillWidth: true

                    text: model.description
                }
            }
        }
    }
}