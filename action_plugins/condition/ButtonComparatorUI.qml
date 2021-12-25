import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import gremlin.action_plugins


Item {
    id: _root

    property ButtonComparator comparator

    implicitHeight: _content.height

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