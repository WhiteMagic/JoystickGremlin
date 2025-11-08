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

import Gremlin.Profile


Item {
    id: _root

    property HatDirectionModel directions

    implicitHeight: _checkboxes.height
    implicitWidth: _checkboxes.width

    RowLayout {
        id: _checkboxes

        IconCheckBox {
            image: "../gfx/hat_n.png"

            checked: directions.hatNorth
            onCheckedChanged: {
                directions.hatNorth = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_ne.png"

            checked: directions.hatNorthEast
            onCheckedChanged: {
                directions.hatNorthEast = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_e.png"

            checked: directions.hatEast
            onCheckedChanged: {
                directions.hatEast = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_se.png"

            checked: directions.hatSouthEast
            onCheckedChanged: {
                directions.hatSouthEast = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_s.png"

            checked: directions.hatSouth
            onCheckedChanged: {
                directions.hatSouth = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_sw.png"

            checked: directions.hatSouthWest
            onCheckedChanged: {
                directions.hatSouthWest = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_w.png"

            checked: directions.hatWest
            onCheckedChanged: {
                directions.hatWest = checked
            }
        }

        IconCheckBox {
            image: "../gfx/hat_nw.png"

            checked: directions.hatNorthWest
            onCheckedChanged: {
                directions.hatNorthWest = checked
            }
        }
    }
}