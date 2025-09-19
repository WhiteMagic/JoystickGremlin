import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Config


Item {

    ActionSequenceOrdering {
        id: _data
    }

    implicitHeight: _content.height

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        ListView {
            model: _data

            delegate: Text {
                text: model.name
            }
        }
    }

}
