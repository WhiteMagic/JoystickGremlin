// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kobold.Foundation

import Gremlin.Device

// Public plugin-facing kit component: vJoy output device + input picker. Same API/wiring as
// the legacy qml/VJoySelector.qml (VJoyDevices model, setInitialState/setState,
// currentSelectionChanged/currentValuesChanged), but built from plain Kobold ComboBoxes --
// no Universal-styled TooltipComboBox, no Base/Compact split (deleted app-wide), no hover
// tooltip. Kobold's own ComboBox popup already fast-scrolls large lists (the same
// wheel-step-3-per-tick technique the legacy ComboBoxScrollableEntries used), so nothing is
// lost for the 100+ entry vJoy device/input lists this exists to handle.
Item {
    id: root

    property alias validTypes: _vjoy.validTypes

    signal selectionChanged(int deviceId, string inputType, int inputId)

    implicitHeight: _content.implicitHeight
    implicitWidth: _content.implicitWidth

    function initialize(vjoyId, inputType, inputId) {
        _vjoy.setInitialState(vjoyId, inputType, inputId)
    }

    function updateState() {
        _vjoy.setState(_deviceCombo.currentText, _inputCombo.currentText)
    }

    VJoyDevices {
        id: _vjoy

        onCurrentSelectionChanged: (vjoyId, inputType, inputId) => {
            root.selectionChanged(vjoyId, inputType, inputId)
        }

        onCurrentValuesChanged: (vjoyName, inputName) => {
            _deviceCombo.currentIndex = _deviceCombo.find(vjoyName)
            _inputCombo.currentIndex = _inputCombo.find(inputName)
        }
    }

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: Metrics.gapM

        // Natural, content-driven width -- not stretched to fill whatever row they end
        // up in (vertical/horizontal space is precious; these show short labels like
        // "vJoy Device 1" / "Axis 1", not paragraphs).
        ComboBox {
            id: _deviceCombo

            model: _vjoy.vjoyDevices

            onActivated: root.updateState()
        }

        ComboBox {
            id: _inputCombo

            model: _vjoy.inputChoices

            onActivated: root.updateState()
        }

        Text {
            visible: !_vjoy.hasValidVJoyDevices
            text: "No vJoy devices available."
            color: Theme.error
            font.family: FontType.sans
            font.pixelSize: Metrics.textBody
        }
    }
}
