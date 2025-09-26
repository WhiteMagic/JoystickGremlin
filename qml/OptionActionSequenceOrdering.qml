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

import Gremlin.Config


Item {
    ActionSequenceOrdering {
        id: _data
    }

    implicitHeight: _content.implicitHeight

    ListView {
        id: _content

        implicitHeight: contentHeight

        model: _data

        delegate: Thing {
            name: model.name
            active: model.visible
        }
    }

    component Thing : RowLayout {
        property alias name: _switch.text
        property alias active: _switch.checked


        IconButton {
            text: bsi.icons.drag_handle
        }
        CompactSwitch {
            id: _switch

            onToggled: () => {
                // if (model.visible !== checked) {
                    model.visible = checked
                // }
                console.log("Toggled", name, " to ", checked)
            }
        }
    }
}
