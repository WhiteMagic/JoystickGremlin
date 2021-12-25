// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2021 Lionel Ott
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

import gremlin.action_plugins


Item {
    id: _root

    property var model

    implicitHeight: Math.max([
        _input_state.height,
        _joystick.height,
        // _vjoy.height,
        // _keyboard.height
    ])

    Loader {
        id: _input_state
        active: _root.model.conditionType == "input-state"

        sourceComponent: InputStateConditionUI {
            model: modelData
        }
    }
    Loader {
        id: _joystick
        active: _root.model.conditionType == "joystick"

        sourceComponent: JoystickConditionUI {
            model: modelData
        }
    }
    // Loader {
    //     id: _vjoy
    //     active: _root.model.conditionType == "vjoy"

    //     sourceComponent: VJoyConditionUI {
    //         model: modelData
    //     }
    // }
    // Loader {
    //     id: _keyboard
    //     active: _root.model.conditionType == "keyboard"

    //     sourceComponent: KeyboardConditionUI {
    //         model: modelData
    //     }
    // }
}