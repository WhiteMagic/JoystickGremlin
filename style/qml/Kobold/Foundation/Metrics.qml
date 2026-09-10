// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma Singleton

import QtQuick

QtObject {
    // Only three scale percentage are valid: 100, 150 and 200.
    readonly property int scalePercentage: themeManager.uiScale
    readonly property real scale: scalePercentage / 100.0

    // Functions computing actual pixel values, taking scale into account.
    function dp(x) { return Math.round(x * scale) }
    function even(x) { let v = Math.round(x * scale); return v % 2 ? v + 1 : v }
    function odd(x) { let v = Math.round(x * scale); return v % 2 ? v : v + 1 }
    function pick(m) { return m[scalePercentage] }

    // Core dimension tokens.
    readonly property int rowInput:      dp(52)
    readonly property int rowAction:     dp(28)
    readonly property int actionSpacing: odd(5)
    readonly property int controlHeight: dp(24)
    // Horizontal indentation of actions.
    readonly property int indent:        dp(24)
    // Used for icons, checkboxes, radio buttons, etc.
    readonly property int icon:          dp(16)
    readonly property int gapS:          dp(4)
    readonly property int gapM:          dp(8)
    readonly property int gapL:          dp(12)
    readonly property int radius:        dp(2)
    // Width used for slider tracks.
    readonly property int sliderTrack:   dp(4)
    readonly property int labelColumn:   dp(250)

    // Font pixel sizes, font families and weight live in FontType.
    readonly property int textBody:      dp(14)
    readonly property int textDetail:    dp(12)

    readonly property real hairline:     pick({100: 1, 150: 1, 200: 2})
    readonly property real accentMark:   pick({100: 2, 150: 2, 200: 4})

    // Dimensions used for the overall layout of the UI.
    readonly property int menuFooterHeight: dp(26)
    readonly property int toolbar:       dp(34)
    readonly property int tabStrip:      dp(36)
    readonly property int windowWidth:   dp(1400)
    readonly property int windowHeight:  dp(900)
    readonly property int leftPaneMin:   dp(400)
    readonly property int rightPaneMin:  dp(900)
    readonly property int inputRowPitch: dp(52)
    readonly property int tabPadding:    dp(48)
    readonly property int actionRowInset: (rowAction - controlHeight) / 2

    // Formatting constants.
    readonly property int preciseDecimalPlaces: 4
    readonly property int defaultDecimalPlaces: 2

    // Constants used in value computations.
    readonly property real _tooltipMaxWidth:  dp(500)
    readonly property real _tooltipPadding:   dp(20)

    function tooltipWidth(contentWidth) {
        return contentWidth > _tooltipMaxWidth ? _tooltipMaxWidth : contentWidth + _tooltipPadding
    }
    function paddedTabButtonWidth(baseWidth) {
        return baseWidth + tabPadding
    }
}
