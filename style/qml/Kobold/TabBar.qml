// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.TabBar {
    id: control

    implicitHeight: Metrics.tabStrip
    implicitWidth: contentItem.contentWidth

    contentItem: ListView {
        implicitWidth: contentWidth
        model: control.contentModel
        currentIndex: control.currentIndex
        spacing: 0
        orientation: ListView.Horizontal
        boundsBehavior: Flickable.StopAtBounds
        snapMode: ListView.SnapToItem
    }

    // Ties the shell frame together with the left-pane well (SPEC bgAlt).
    background: Rectangle {
        color: Theme.bgAlt
    }
}
