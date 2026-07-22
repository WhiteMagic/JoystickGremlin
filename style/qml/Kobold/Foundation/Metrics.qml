// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma Singleton

import QtQuick

QtObject {
    readonly property int scalePercentage: themeManager.uiScale // 100 | 150 | 200
    readonly property real scale: scalePercentage / 100.0

    // Policies -- pick one per token.
    function dp(x) { return Math.round(x * scale) }
    function even(x) { let v = Math.round(x * scale); return v % 2 ? v + 1 : v }
    function pick(m) { return m[scalePercentage] }

    // Core dimension tokens (SPEC §4).
    readonly property int rowInput:      dp(48)
    readonly property int rowAction:     dp(28)
    readonly property int ctrlH:         dp(24)
    readonly property int indent:        dp(16)
    readonly property int icon:          dp(16)
    readonly property int markSize:      dp(16) // CheckBox box / RadioButton ring diameter
    readonly property int gapS:          dp(4)
    readonly property int gapM:          dp(8)
    readonly property int gapL:          dp(12)
    readonly property int radius:        dp(2)

    // Font pixel sizes (family/weight live in FontType).
    readonly property int textBody:      dp(14)
    readonly property int textDetail:    dp(12)

    // Hand-controlled exceptions -- kept off the even/dp policy, per SPEC §4.
    readonly property real hairline:      pick({100: 1, 150: 1, 200: 2})
    readonly property real insertionLine: pick({100: 2, 150: 2, 200: 4})
    readonly property real accentMark:    pick({100: 2, 150: 2, 200: 4}) // tab underline, selected-row bar
    readonly property int  indentGuide:   pick({100: 1, 150: 2, 200: 2})

    // Shell heights, pane minimums (SPEC §10 / guide §3.2).
    readonly property int menuBar:       dp(26)
    readonly property int toolbar:       dp(34)
    readonly property int tabStrip:      dp(36)
    readonly property int footer:        dp(24)
    readonly property int bodyMin:       dp(780)
    readonly property int windowWidth:   dp(1400)
    readonly property int windowHeight:  dp(900)
    readonly property int leftPaneMin:   dp(400)
    readonly property int rightPaneMin:  dp(900)
    readonly property int inputRowPitch: dp(52) // rowInput (48) + gapS (4)
}
