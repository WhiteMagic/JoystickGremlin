// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T

import Kobold.Foundation

T.ProgressBar {
    id: control

    // T.ProgressBar has no orientation of its own; values are Qt.Horizontal / Qt.Vertical.
    property int orientation: Qt.Horizontal
    // Thickness across the bar -- the length comes from the layout.
    property int barSize: Metrics.icon
    // State readouts (live axis values) override this with Theme.line for a denser track.
    property color trackColor: Theme.bgAlt

    readonly property bool vertical: orientation === Qt.Vertical
    // The only place indeterminate is handled, so the geometry below never branches on it.
    readonly property real fillFraction: control.indeterminate ? 1 : control.visualPosition

    implicitWidth: vertical ? barSize : Metrics.controlHeight * 6
    implicitHeight: vertical ? Metrics.controlHeight * 6 : barSize

    padding: Metrics.dp(2)

    background: Rectangle {
        radius: Metrics.radius
        color: control.trackColor
        border.width: Metrics.hairline
        border.color: Theme.line
    }

    contentItem: Item {
        Rectangle {
            // Vertical bars grow upward from the bottom edge.
            anchors.left: parent.left
            anchors.bottom: parent.bottom

            width: control.vertical ? parent.width : control.fillFraction * parent.width
            height: control.vertical ? control.fillFraction * parent.height : parent.height
            radius: Metrics.radius
            color: control.indeterminate ? Theme.fgDisabled : Theme.accent
        }
    }
}
