import QtQuick 2.14
import QtQuick.Controls 2.14
import QtQuick.Layouts 1.14

import gremlin.action_plugins 1.0


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