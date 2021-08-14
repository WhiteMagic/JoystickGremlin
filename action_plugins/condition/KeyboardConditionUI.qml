import QtQuick 2.14
import QtQuick.Controls 2.14
import QtQuick.Layouts 1.14
import QtQuick.Window 2.14

import gremlin.action_plugins 1.0

Item {
    id: _root

    implicitHeight: _button.height

    property KeyboardCondition model

    Loader {
        id: _button

        active: _root.model.inputType == "button"

        sourceComponent: RowLayout {
            anchors.left: parent.left
            anchors.right: parent.right

            Label {
                text: "This input is"
            }

        }
    }
}