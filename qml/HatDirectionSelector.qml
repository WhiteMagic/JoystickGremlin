// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2019 Lionel Ott
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


import QtQuick 2.14
import QtQuick.Controls 2.14


Item {
    id: root

    Row {
        CheckBox {
            //text: "N"
            icon {
                source: "gfx/button_delete.png"
            }
        }

        CheckBox {
            text: "NE"
        }

        CheckBox {
            text: "E"
        }

        CheckBox {
            text: "SE"
        }

        CheckBox {
            text: "S"
        }

        CheckBox {
            text: "SW"
        }

        CheckBox {
            text: "W"
        }

        CheckBox {
            text: "NW"
        }
    }

}