// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Profile

Item {
    id: _root

    property InputItemBindingModel inputBinding

    implicitWidth: _content.width
    implicitHeight: _content.height

    RowLayout {
        id: _content

        visible: !["button", "key"].includes(_root.inputBinding.inputType)

        Label {
            leftPadding: 20
            text: "Treat as"
        }

        RadioButton {
            text: "Button"

            checked: _root.inputBinding.behavior == "button"
            onClicked: () => { _root.inputBinding.behavior = "button" }
        }

        RadioButton {
            text: "Axis"

            visible: _root.inputBinding.inputType == "axis"

            checked: _root.inputBinding.behavior == "axis"
            onClicked: () => { _root.inputBinding.behavior = "axis" }
        }

        RadioButton {
            text: "Hat"

            visible: _root.inputBinding.inputType == "hat"

            checked: _root.inputBinding.behavior == "hat"
            onClicked: () => { _root.inputBinding.behavior = "hat" }
        }
    }
}
