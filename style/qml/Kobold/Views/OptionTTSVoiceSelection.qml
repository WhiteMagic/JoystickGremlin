// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls

import Gremlin.Config

Item {
    id: _root

    implicitHeight: _combo.implicitHeight
    implicitWidth: _combo.implicitWidth

    TTSVoiceSelectionModel {
        id: _model
    }

    ComboBox {
        id: _combo

        anchors.fill: parent

        model: _model
        textRole: "name"
        currentIndex: _model.currentIndex

        onActivated: (index) => { _model.currentIndex = index }
    }
}
