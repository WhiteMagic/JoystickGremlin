// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma Singleton

import QtQuick
import QtQuick.Controls.Universal

Item {
    function removeAlpha(color) {
        return Qt.rgba(color.r, color.g, color.b, 1.0)
    }

    // One of "Light", "Dark" (soft charcoal), or "High Contrast Dark"
    // (pure black/white). Set from backend.colorMode in Main.qml.
    property string colorMode: "Light"

    property bool isHighContrast: colorMode === "High Contrast Dark"
    property bool isDarkMode: colorMode !== "Light"

    // Color definitions.
    property var accent: Universal.accent
    property var theme: isDarkMode ? Universal.Dark : Universal.Light

    // The soft "Dark" mode uses an explicit charcoal palette; "High Contrast
    // Dark" keeps the original pure-black/white behavior; "Light" is unchanged.
    property var background: colorMode === "Dark"
        ? "#1E1E1E"
        : (isDarkMode ? Universal.foreground : Universal.background)
    property var foreground: colorMode === "Dark"
        ? "#D4D4D4"
        : (isDarkMode ? Universal.background : Universal.foreground)
    property var backgroundShade: colorMode === "Dark"
        ? "#252526"
        : (isDarkMode ? Qt.tint(background, "#40ffffff") : Qt.tint(foreground, "#b0ffffff"))
    property var lowColor: isDarkMode ? Qt.hsva(0.0, 0.0, 0.2, 1.0) : Qt.hsva(0.0, 0.0, 0.8, 1.0)
    property var medColor: isDarkMode ? Qt.hsva(0.0, 0.0, 0.4, 1.0) : Qt.hsva(0.0, 0.0, 0.6, 1.0)
    property var error: "#A20025"
    property var warning: "#F0A30A"

    // Spinbox presets.
    property int decimalsPrecise: 4
    property int decimalsStandard: 2
}
