// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T

import Kobold.Foundation

T.Menu {
    id: control

    // Default matches ComboBox's popu, overridable per-instance.
    property color fillColor: Theme.bgAlt

    margins: 0
    padding: 0
    implicitWidth: Metrics.controlHeight * 8
    implicitHeight: contentItem.implicitHeight

    contentItem: ListView {
        implicitHeight: contentHeight
        model: control.contentModel
        interactive: false
        clip: true
        currentIndex: control.currentIndex
    }

    background: Rectangle {
        color: control.fillColor
        border.width: Metrics.hairline
        border.color: Theme.line
    }
}
