// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls

import Gremlin.Device

// Replaces qml/LogicalDeviceSelector.qml, which loaded Base.TooltipComboBox /
// Compact.TooltipComboBox -- both from the now-deleted theme/Gremlin kit. There is
// only one Kobold style, so the old base/compact variant switch is gone too: a
// single stock ComboBox, already reskinned by the Kobold style.
Item {
    id: root

    property string logicalInputType
    property alias currentIndex: _model.currentIndex
    property alias logicalInputIdentifier: _model.currentIdentifier
    property alias validTypes: _model.validTypes

    implicitWidth: _selection.implicitWidth
    implicitHeight: _selection.implicitHeight

    LogicalDeviceSelectorModel {
        id: _model
    }

    ComboBox {
        id: _selection

        anchors.left: parent.left
        anchors.right: parent.right
        implicitWidth: Math.max(implicitContentWidth + leftPadding + rightPadding, 200)

        model: _model
        textRole: "label"
        currentIndex: _model.currentIndex

        onActivated: (index) => {
            if (_model.currentIndex !== index) {
                _model.currentIndex = index
            }
        }
    }
}
