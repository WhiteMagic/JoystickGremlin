// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import Compact as Compact

Compact.ComboBox {
    property bool isPressed: true
    signal stateModified(bool isPressed)

    model: ["Press", "Release"]

    onActivated: () => { stateModified(currentText === "Press") }
    onIsPressedChanged: () => { currentIndex = isPressed ? 0 : 1 }
}
