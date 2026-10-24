// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls

import Gremlin.Config
import Gremlin.UI

Item {
    id: _root

    readonly property ThemeSelectionModel _model: ModelFactory.themeSelectionModel(_root)

    implicitHeight: _combo.implicitHeight
    implicitWidth: _combo.implicitWidth

    ComboBox {
        id: _combo

        anchors.fill: parent

        model: _root._model
        textRole: "name"
        currentIndex: _root._model.currentIndex

        onActivated: (index) => { _root._model.currentIndex = index }
    }
}
