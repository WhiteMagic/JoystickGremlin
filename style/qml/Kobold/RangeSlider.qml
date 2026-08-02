// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

// Flagged spec deviation: the filled span between the two handles uses Theme.accent, which
// isn't in SPEC §3's enumerated "accent's complete inventory" -- a necessary extension, since
// there's no other way to show a *selected range* with only 11 tokens. Confirmed with the user.
T.RangeSlider {
    id: control

    implicitWidth: Metrics.controlHeight * 6
    implicitHeight: Metrics.controlHeight

    background: Rectangle {
        x: control.leftPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        width: control.availableWidth
        height: Metrics.sliderTrack
        radius: height / 2
        color: Theme.bgAlt
        border.width: Metrics.hairline
        border.color: Theme.line

        Rectangle {
            x: control.first.visualPosition * parent.width
            width: (control.second.visualPosition - control.first.visualPosition) * parent.width
            height: parent.height
            radius: height / 2
            color: Theme.accent
        }
    }

    first.handle: Rectangle {
        x: control.leftPadding + control.first.visualPosition * (control.availableWidth - width)
        y: control.topPadding + (control.availableHeight - height) / 2
        width: Metrics.icon
        height: Metrics.icon
        radius: width / 2
        color: Theme.bg
        border.width: Metrics.hairline
        border.color: control.first.pressed ? Theme.accent : Theme.line
    }

    second.handle: Rectangle {
        x: control.leftPadding + control.second.visualPosition * (control.availableWidth - width)
        y: control.topPadding + (control.availableHeight - height) / 2
        width: Metrics.icon
        height: Metrics.icon
        radius: width / 2
        color: Theme.bg
        border.width: Metrics.hairline
        border.color: control.second.pressed ? Theme.accent : Theme.line
    }
}
