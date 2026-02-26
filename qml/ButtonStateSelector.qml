// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick.Controls

ComboBox {
    property bool isPressed: true

    model: ["Press", "Release"]

    onActivated: () => { isPressed = currentText === "Press" }
    onIsPressedChanged: () => { currentIndex = isPressed ? 0 : 1 }
}