// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Kobold.Foundation

Window {
    id: _root

    height: Metrics.tabStrip
    width: Metrics.labelColumn * 1.5

    color: Theme.bg

    signal accepted(string value)
    property string text : "New text"
    property var validator: function(value) { return true }

    onTextChanged: () =>  { _input.focus = true }

    title: "Text Input Field"

    TextMetrics {
        id: _textMetrics

        font: _input.font
        text: _root.text
    }

    RowLayout {
        id: _content

        anchors.fill: parent

        TextField {
            id: _input

            Layout.leftMargin: Metrics.gapS
            Layout.fillWidth: true

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

            Layout.rightMargin: Metrics.gapM

            text: "Ok"

            onClicked: () => { _root.accepted(_input.text) }
        }
    }

}
