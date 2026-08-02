// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma Singleton

import QtQuick

QtObject {
    readonly property string appearance: themeManager.appearance
    readonly property bool isDarkTheme: themeManager.appearance === "dark"

    readonly property color bg:         themeManager.bg
    readonly property color bgAlt:      themeManager.bgAlt
    readonly property color bgHover:    themeManager.bgHover
    readonly property color bgSelected: themeManager.bgSelected
    readonly property color line:       themeManager.line
    readonly property color fg:         themeManager.fg
    readonly property color fgMuted:    themeManager.fgMuted
    readonly property color fgDisabled: themeManager.fgDisabled
    readonly property color accent:     themeManager.accent
    readonly property color error:      themeManager.error
    readonly property color warning:    themeManager.warning
}
