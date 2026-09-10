// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Kobold.Foundation

// Behaves similar to a ListView, however, does not perform delegate destruction and
// reuse based on visibility. This is necessary for instances where items should not
// be destroyed or recreated.
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
