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

import Gremlin.ActionPlugins


Item {
    id: _root

    property PressedComparator comparator

    implicitHeight: _content.height
    implicitWidth: _content.width

    RowLayout {
        id: _content

        Label {
            text: "This input is"
        }

        ComboBox {
            model: ["Pressed", "Released"]
            onActivated: {
                _root.comparator.isPressed = currentValue
            }
            Component.onCompleted: {
                currentIndex = indexOfValue(_root.comparator.isPressed)
            }
        }
    }
}