// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls

import Gremlin.Device
import Gremlin.UI

// UI element to select a logical device input.
Item {
    id: root

    property string logicalInputType
    property var validTypes: []
    property InputIdentifier logicalInputIdentifier

    readonly property LogicalDeviceSelectorModel _model:
        ModelFactory.logicalDeviceSelectorModel(root)
    // Valid types have to reach the model before the identifier does.
    property bool _ready: false

    signal logicalInputSelected(InputIdentifier identifier)

    implicitWidth: _selection.implicitWidth
    implicitHeight: _selection.implicitHeight

    onValidTypesChanged: () => { if (_ready) _model.validTypes = validTypes }
    onLogicalInputIdentifierChanged: () => {
        if (_ready && logicalInputIdentifier) {
            _model.currentIdentifier = logicalInputIdentifier
        }
    }

    Component.onCompleted: () => {
        _model.validTypes = validTypes
        if (logicalInputIdentifier) {
            _model.currentIdentifier = logicalInputIdentifier
        }
        _ready = true
    }

    Connections {
        target: root._model

        function onSelectionChanged() {
            root.logicalInputSelected(root._model.currentIdentifier)
        }
    }

    ComboBox {
        id: _selection

        anchors.left: parent.left
        anchors.right: parent.right
        implicitWidth: implicitContentWidth + leftPadding + rightPadding

        model: root._model
        textRole: "label"
        currentIndex: root._model.currentIndex

        onActivated: (index) => {
            if (root._model.currentIndex !== index) {
                root._model.currentIndex = index
            }
        }
    }
}
