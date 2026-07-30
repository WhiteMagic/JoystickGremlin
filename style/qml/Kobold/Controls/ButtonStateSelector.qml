// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick.Controls

// Press/Release selector for button-triggered comparisons and macro steps.
ComboBox {
    id: root

    property bool isPressed: true
    signal stateModified(bool isPressed)

    model: ["Press", "Release"]

    onActivated: () => { root.stateModified(currentText === "Press") }
    onIsPressedChanged: () => { currentIndex = isPressed ? 0 : 1 }
}
