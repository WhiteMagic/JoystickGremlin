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
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.ActionPlugins
import "../../qml"


Item {
    id: _root

    implicitHeight: _content.height

    property VJoyCondition model
    property var comparatorUi: null

    function updateComparatorUi() {
        if(!model.comparator) {
            return;
        }
        if(comparatorUi !== null) {
            comparatorUi.destroy();
        }

        var qml_string = "";
        if(model.comparator.typeName == "pressed") {
            qml_string = `PressedComparatorUI {comparator: model.comparator}`;
        }
        else if(model.comparator.typeName == "range") {
            qml_string = `RangeComparatorUI {comparator: model.comparator}`;
        }
        else if(model.comparator.typeName == "direction") {
            qml_string = `DirectionComparatorUI {comparator: model.comparator}`;
        }
        comparatorUi = Qt.createQmlObject(qml_string, _comparator, "Comparator");
        _comparator.implicitHeight = comparatorUi.implicitHeight;
        _comparator.implicitWidth = comparatorUi.implicitWidth;
    }

    // Load appropriate comparator UI element.
    Component.onCompleted: () => { updateComparatorUi(); }

    // React to model changes.
    Connections {
        target: model

        // Change comparator UI element when needed.
        function onComparatorChanged() {
            updateComparatorUi()
        }
    }

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        RowLayout {
            Label {
                Layout.preferredWidth: 150
                text: "vJoy Condition"
            }

            VJoySelector {
                validTypes: ["axis", "button", "hat"]

                onVjoyInputIdChanged: { _root.model.vjoyInputId = vjoyInputId }
                onVjoyDeviceIdChanged: { _root.model.vjoyDeviceId = vjoyDeviceId }
                onVjoyInputTypeChanged: { _root.model.vjoyInputType = vjoyInputType }

                Component.onCompleted: {
                    vjoyInputType = _root.model.vjoyInputType
                    vjoyInputId = _root.model.vjoyInputId
                    vjoyDeviceId = _root.model.vjoyDeviceId
                }
            }

            Item {
                id: _comparator
            }
        }
    }
}