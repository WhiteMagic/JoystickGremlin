// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls

import Kobold.Foundation

// Vertical list with pixel-based wheel scrolling to handle long lists consistently.
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

    // Scroll events are converted into amount of pixels to move the underlying content.
    // The amount scrolled is tunable via wheelStep. This overrides the default scroll
    // behavior of the ListView as it is unsuitable for lists with many entries.
    WheelHandler {
        onWheel: (event) => {
            const delta = -(event.angleDelta.y / 120) * _list.wheelStep
            _list.contentY = Math.max(
                0,
                Math.min(_list.contentY + delta, Math.max(0, _list.contentHeight - _list.height))
            )
            event.accepted = true
        }
    }
}
