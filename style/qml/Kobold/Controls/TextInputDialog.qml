// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Kobold.Foundation

Window {
    id: _root

    minimumWidth: 200
    minimumHeight: 60

    color: Theme.bg

    signal accepted(string value)
    property string text : "New text"
    property var validator: function(value) { return true }

    onTextChanged: () =>  { _input.focus = true }

    title: "Text Input Field"

    RowLayout {
        anchors.fill: parent

        TextField {
            id: _input

            Layout.fillWidth: true
            Layout.leftMargin: 5

            text: _root.text

            onTextEdited: () => {
                let isValid = _root.validator(text)
                _errorIcon.visible = !isValid
                _button.enabled = isValid
            }
        }

        AppIcon {
            id: _errorIcon

            visible: false
            name: "error"
            role: "error"
        }

        Button {
            id: _button

            Layout.rightMargin: 10

            text: "Ok"

            onClicked: () => { _root.accepted(_input.text) }
        }
    }

}
