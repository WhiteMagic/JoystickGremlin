// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Kobold.Foundation

ProgressBar {
    id: control

    enum Orientation {
        Horizontal,
        Vertical
    }

    value: 0
    padding: 2

    property int barSize: Metrics.icon
    property int orientation: BetterProgressBar.Orientation.Horizontal

    // Private indicator property
    property bool __isHorizontal: orientation === BetterProgressBar.Orientation.Horizontal

    background: Rectangle {
        implicitHeight: __isHorizontal ? barSize : height
        implicitWidth: __isHorizontal ? width : barSize

        radius: Metrics.radius
        color: Theme.line
    }

    contentItem: Item {
        implicitHeight: __isHorizontal ? barSize - 2 : height
        implicitWidth: __isHorizontal ? width : barSize - 2

        Rectangle {
            anchors.bottom: parent.bottom

            height: __isHorizontal ? parent.height : control.visualPosition * parent.height
            width: __isHorizontal ? control.visualPosition * parent.width : parent.width
            radius: 2
            color: Theme.accent
        }
    }
}