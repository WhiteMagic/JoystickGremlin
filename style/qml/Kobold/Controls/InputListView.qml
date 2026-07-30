// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls

// Kobold-owned equivalent of qml/JGListView.qml. Lives in Kobold.Controls (not
// Internal) so both the app's own input panels and action-plugin config bodies
// share one implementation. Named distinctly (not "ListView") because a
// bare "ListView" defined in this module would be silently shadowed by
// QtQuick's own ListView wherever a consumer also imports QtQuick.
ListView {
    id: _list

    property bool scrollbarAlwaysVisible: false
    property int scrollStep: 3

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
