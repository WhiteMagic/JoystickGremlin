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

import Gremlin.ActionPlugins
import Gremlin.Util

import "../../qml"


Item {
    id: _root

    function formatInputs(data)
    {
        var text = "<ul>";
        data.forEach(function(entry) {
            text += "<li>" + entry + "</li>";
        })
        text += "</ul>";
        return text;
    }

    property JoystickCondition model
    property string conditionText: formatInputs(model.inputs)

    implicitHeight: _content.height

    // Format the condition inputs as an unordered list
    Connections {
        target: model
        function onInputsChanged(data)
        {
            _root.conditionText = formatInputs(data);
        }
        // function onComparatorChanged()
        // {
        //     if(model.comparator)
        //     {
        //         _comparator.sourceComponent = Qt.createQmlObject(`
        //             PressedComparatorUI {
        //                 comparator: model.comparator
        //             }`,
        //             _comparator,
        //             "ComparatorUI"
        //         );
        //     }
        //     else
        //     {
        //         _comparator.sourceComponent = undefined;
        //     }
        // }
    }

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        RowLayout {
            // FIXME: this likely needs to be moved inside the loaders as it  will
            //        be input type specific as well
            Label {
                Layout.preferredWidth: 150

                text: "Joystick Condition"
            }

            // Loaders for the specific types of inputs
            Loader {
                active: _root.model.comparator && _root.model.comparator.typeName == "pressed"

                sourceComponent: PressedComparatorUI {
                    comparator: _root.model.comparator
                }
            }
            Loader {
                active: _root.model.comparator && _root.model.comparator.typeName == "range"

                sourceComponent: RangeComparatorUI {
                    comparator: _root.model.comparator
                }
            }
            Loader {
                active: _root.model.comparator && _root.model.comparator.typeName == "direction"

                sourceComponent: DirectionComparatorUI {
                    comparator: _root.model.comparator
                }
            }

            InputListener {
                id: _tmp
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignRight

                callback: _root.model.updateInputs
                multipleInputs: true
                eventTypes: ["axis", "button", "hat"]
            }
        }

        RowLayout {
            Label {
                Layout.fillWidth: true

                text: _root.conditionText
            }
        }
    }
}