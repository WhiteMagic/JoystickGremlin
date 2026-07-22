// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.Menu {
    id: control

    margins: 0
    padding: 0
    // ListView doesn't aggregate implicit size from its delegates, and Popup
    // doesn't propagate contentItem's implicit size on its own -- without both,
    // the popup opens (visible: true) but renders at zero size, invisibly.
    implicitWidth: Metrics.ctrlH * 8
    implicitHeight: contentItem.implicitHeight

    contentItem: ListView {
        implicitHeight: contentHeight
        model: control.contentModel
        interactive: false
        clip: true
        currentIndex: control.currentIndex
    }

    // No shadow, no elevation (R2): opaque bgAlt fill + 1px line border, same as ComboBox's popup.
    background: Rectangle {
        color: Theme.bgAlt
        border.width: Metrics.hairline
        border.color: Theme.line
    }
}
