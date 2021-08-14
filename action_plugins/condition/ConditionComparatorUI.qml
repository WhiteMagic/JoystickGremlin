import QtQuick 2.14
import QtQuick.Controls 2.14
import QtQuick.Layouts 1.14
import QtQuick.Window 2.14

import gremlin.action_plugins 1.0


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