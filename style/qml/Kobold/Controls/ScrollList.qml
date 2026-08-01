// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import Kobold.Foundation

// Vertical list with pixel-based wheel scrolling. Named "ScrollList", never "ListView" --
// a bare "ListView" defined in this module would be silently shadowed by QtQuick's own
// ListView wherever a consumer also imports QtQuick.
ListView {
    id: _list

    property bool scrollbarAlwaysVisible: true
    property real wheelStep: Metrics.inputRowPitch * 3
    property alias scrollBar: _scrollBar

    // Prevent content being shown outside the widget's bounds.
    clip: true

    ScrollBar.vertical: ScrollBar {
        id: _scrollBar
        policy: scrollbarAlwaysVisible ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
    }
    // Disable mobile device scrolling behaviors.
    flickableDirection: Flickable.VerticalFlick
    boundsBehavior: Flickable.StopAtBounds

    // Pixel wheel scroll, tunable via wheelStep -- replaces index-jump scrolling, which
    // only worked for short, uniform-height rows and hard-errors on a delegate taller
    // than the viewport (positionViewAtIndex has nothing to move to).
    WheelHandler {
        onWheel: (event) => {
            const delta = event.angleDelta.y > 0 ? -_list.wheelStep : _list.wheelStep
            _list.contentY = Math.max(
                0,
                Math.min(_list.contentY + delta, Math.max(0, _list.contentHeight - _list.height))
            )
            event.accepted = true
        }
    }
}
