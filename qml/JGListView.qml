// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls


ListView {
    id: _list

    property bool scrollbarAlwaysVisible: false
    property int scrollStep: 3
    // Index-jump scrolling only suits many short, uniform-height rows (device/input lists,
    // popups). A delegate taller than the viewport (e.g. one action-sequence tree) can't be
    // scrolled into view by jumping whole indices -- positionViewAtIndex has nothing to move
    // to. Callers with tall/variable delegates set this false to fall back to the ListView's
    // native per-pixel wheel flicking.
    property bool stepScroll: true

    // Prevent content being shown outside the widget's bounds.
    clip: true

    // Scrollbar visibility behavior as configured.
    ScrollBar.vertical: ScrollBar {
        policy: scrollbarAlwaysVisible ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
    }
    // Disable mobile device scrolling behaviors.
    flickableDirection: Flickable.VerticalFlick
    boundsBehavior: Flickable.StopAtBounds

    // Step-scroll instead of the default kinetic/momentum wheel flick.
    WheelHandler {
        enabled: _list.stepScroll

        onWheel: (event) => {
            const topIndex = Math.max(0, _list.indexAt(0, _list.contentY + 1))
            if (event.angleDelta.y > 0) {
                _list.positionViewAtIndex(
                    Math.max(0, topIndex - _list.scrollStep),
                    ListView.Beginning
                )
            } else {
                _list.positionViewAtIndex(
                    Math.min(_list.count - 1, topIndex + _list.scrollStep),
                    ListView.Beginning
                )
            }
            event.accepted = true
        }
    }
}