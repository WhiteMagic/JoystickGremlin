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
import Qt.labs.qmlmodels

import Gremlin.Config


Item {
    id: _root

    property ConfigGroupModel groupModel

    Repeater {
        id: _groupView

        width: parent.width
        height: parent.height

        model: groupModel
        delegate: _groupDelegate
    }

    Component {
        id: _groupDelegate

        Item {
            required property int index
            required property ConfigEntryModel entryModel

            width: _groupView.width
            height: 200//_entryView.height

            // title: "Something" + index

            Column {
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

            Row {
                Label {
                    text: model.description
                }
                Switch {
                    checked: model.value

                    onToggled: function() {
                        model.value = checked
                    }
                }
            }
        }
        DelegateChoice {
            roleValue: "string"

            Row {
                Label {
                    text: model.description
                }
            }
        }
        DelegateChoice {
            roleValue: "float"

            Row {
                Label {
                    text: model.description
                }
                FloatSpinBox {
                    realValue: model.value

                    onRealValueModified: function() {
                        model.value = realValue
                    }
                }
            }
        }
        DelegateChoice {
            roleValue: "int"

            Row {
                Label {
                    text: model.description
                }
                SpinBox {
                    value: model.value

                    onValueModified: function() {
                        model.value = value
                    }
                }
            }
        }
    }
}