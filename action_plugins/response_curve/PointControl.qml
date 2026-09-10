// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls

import Kobold.Foundation
import "render_helpers.js" as RH


Rectangle {
    id: _control

    readonly property int offset: 5
    property Repeater repeater
    property Item focusTarget

    width: offset * 2
    height: offset * 2
    radius: offset

    color: action.selectedPoint === index ? Theme.accent : Theme.line

    x: map2u(modelData.center.x)
    y: map2v(modelData.center.y)

    MouseArea {
        anchors.fill: parent
        preventStealing: true

        onPositionChanged: (evt) => {
            let coord = updateControlPoint(parent, evt, index)
            if(coord !== null) {
                action.setControlPoint(coord[0], coord[1], index, true)
            }
        }
        onPressed: () => {
            action.selectedPoint = index
            focusTarget.forceActiveFocus()
        }
        onReleased: () => { action.redrawElements() }
    }
}
