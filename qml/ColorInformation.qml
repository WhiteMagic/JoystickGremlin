// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls.Universal
import Gremlin.Style

Item {
    objectName: "colorInformation"

    Universal.theme: Style.theme

    // Capture color values of interest from the Universal theme to expose to
    // Python.
    property color accent: Universal.accent
    property color background: Universal.background
    property color foreground: Universal.foreground
    property bool isDarkTheme: Universal.theme === Universal.Dark
}
