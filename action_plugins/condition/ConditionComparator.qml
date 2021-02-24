import QtQuick 2.14
import QtQuick.Controls 2.14
import QtQuick.Layouts 1.14
import QtQuick.Window 2.14

Item {
    id: _root

    property var model

    implicitHeight: _content.height

    Loader {
        id: _content
        active: _root.model.conditionType == "input-state"

        sourceComponent: InputTypeCondition {
            model: modelData
        }
    }
}