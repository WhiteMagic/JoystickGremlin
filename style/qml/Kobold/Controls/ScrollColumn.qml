// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kobold.Foundation

// Vertical scroller that realizes all of its content immediately, unlike ScrollList
// (ListView), which creates/destroys delegates as they enter/leave the viewport. Use
// this instead of ScrollList when content is built asynchronously (e.g. a Loader
// resolving via Qt.createComponent) -- ListView-style virtualization re-triggers that
// async settle every time a delegate scrolls into view, which thrashes contentHeight.
// Only suitable for modest item counts, since nothing here is virtualized.
Flickable {
    id: _flickable

    property bool scrollbarAlwaysVisible: true
    property real wheelStep: Metrics.inputRowPitch * 3
    property alias scrollBar: _scrollBar
    default property alias contentData: _column.data

    contentWidth: width
    contentHeight: _column.implicitHeight

    clip: true

    ScrollBar.vertical: ScrollBar {
        id: _scrollBar
        policy: scrollbarAlwaysVisible ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
    }

    flickableDirection: Flickable.VerticalFlick
    boundsBehavior: Flickable.StopAtBounds

    // See ScrollList for the rationale behind pixel-based, magnitude-scaled wheel
    // scrolling instead of index-jump scrolling.
    WheelHandler {
        onWheel: (event) => {
            const delta = -(event.angleDelta.y / 120) * _flickable.wheelStep
            _flickable.contentY = Math.max(
                0,
                Math.min(_flickable.contentY + delta, Math.max(0, _flickable.contentHeight - _flickable.height))
            )
            event.accepted = true
        }
    }

    ColumnLayout {
        id: _column
        width: _flickable.width
    }
}
