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

import QtQuick.Controls.Universal

import Gremlin.Config


Item {
    id: _root

    width: _content.width
    height: _content.height

    property string data_type
    property var something

    Row {
        id: _content

        Loader {
            property alias propertyValue: _root.something
            active: data_type == "bool"
            sourceComponent: _boolWidget
        }

        Loader {
            // property int propertyValue: _root.value
            active: data_type == "int"
            sourceComponent: _intWidget
        }
        Loader {
            // property double propertyValue: _root.value
            active: data_type == "float"
            sourceComponent: _floatWidget
        }
    }

    // Definition of the various widgets allowing properties to be modified
    Component {
        id: _boolWidget

        Switch {
            checked: propertyValue

            onToggled: function() {
                // _root.something = checked
                propertyValue = checked
            }
        }
    }

    Component {
        id: _intWidget

        SpinBox {
            // value: propertyValue
        }
    }

    Component {
        id: _floatWidget

        FloatSpinBox {
            // value: propertyValue
        }
    }
}