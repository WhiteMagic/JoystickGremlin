// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts

import Gremlin.Profile


Item {
    id: _root

    property ActionModel actionNode
    property var callback: null

    implicitHeight: _content.height
    implicitWidth: _button.width + _combobox.width + 13

    Connections {
        target: actionNode

        function onActionChanged() {
            _combobox.model = actionNode.compatibleActions
        }
    }

    onActionNodeChanged: {
        _combobox.model = actionNode.compatibleActions
    }

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        Button {
            id: _button

            Layout.leftMargin: 8
            text: "Add Action"

            onClicked: {
                _root.callback(_combobox.currentText)
            }
        }

        ComboBox {
            id: _combobox

            implicitContentWidthPolicy: ComboBox.WidestText
        }
    }
}