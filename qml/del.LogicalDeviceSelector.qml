// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Base as Base
import Gremlin.Compact as Compact
import Gremlin.Device


Item {
    id: _root

    property bool useCompact: false
    property string logicalInputType

    property alias currentIndex: _model.currentIndex
    property alias logicalInputIdentifier: _model.currentIdentifier
    property alias validTypes: _model.validTypes

    implicitHeight: _content.height
    implicitWidth: _content.implicitWidth

    Component { id: _baseVariant;    Base.TooltipComboBox    {} }
    Component { id: _compactVariant; Compact.TooltipComboBox {} }

    LogicalDeviceSelectorModel {
        id: _model
    }

    Connections {
        target: _loader.item

        function onActivated(index) {
            if (_model.currentIndex !== index) {
                _model.currentIndex = index
            }
        }
    }

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        Loader {
            id: _loader

            Layout.minimumWidth: 200
            Layout.fillWidth: true

            sourceComponent: _root.useCompact ? _compactVariant : _baseVariant

            onLoaded: {
                item.width        = Qt.binding(() => _loader.width)
                item.model        = Qt.binding(() => _model)
                item.textRole     = "label"
                item.currentIndex = Qt.binding(() => _model.currentIndex)
            }
        }
    }

}
