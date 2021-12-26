// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2020 Lionel Ott
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

import Gremlin.Profile


Item {
    id: _root

    property VirtualButtonModel virtualButton

    height: _checkboxes.height
    width: _checkboxes.width

    Row {
        id: _checkboxes

        spacing: 10

        IconCheckBox {
            image: "../gfx/hat_n.png"

            checked: virtualButton.hatNorth
            onCheckedChanged: {
                virtualButton.hatNorth = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_ne.png"

            checked: virtualButton.hatNorthEast
            onCheckedChanged: {
                virtualButton.hatNorthEast = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_e.png"

            checked: virtualButton.hatEast
            onCheckedChanged: {
                virtualButton.hatEast = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_se.png"

            checked: virtualButton.hatSouthEast
            onCheckedChanged: {
                virtualButton.hatSouthEast = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_s.png"

            checked: virtualButton.hatSouth
            onCheckedChanged: {
                virtualButton.hatSouth = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_sw.png"

            checked: virtualButton.hatSouthWest
            onCheckedChanged: {
                virtualButton.hatSouthWest = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_w.png"

            checked: virtualButton.hatWest
            onCheckedChanged: {
                virtualButton.hatWest = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_nw.png"

            checked: virtualButton.hatNorthWest
            onCheckedChanged: {
                virtualButton.hatNorthWest = checked
            }
        }
    }
}