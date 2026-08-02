// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Templates as T
import Kobold.Foundation

T.TabBar {
    id: control

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            contentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset,
                             contentHeight + topPadding + bottomPadding)

    // Scroll-affordance state for external arrow buttons -- true only while
    // there is more content to reveal in that direction. Read through
    // contentItem (a TabBar/Flickable property) rather than an id, so this
    // stays a same-scope self-reference instead of reaching into the nested
    // ListView.
    property bool canScrollBackward: !contentItem.atXBeginning
    property bool canScrollForward: !contentItem.atXEnd

    contentItem: ListView {
        model: control.contentModel
        currentIndex: control.currentIndex

        spacing: control.spacing
        orientation: ListView.Horizontal
        boundsBehavior: Flickable.StopAtBounds
        flickableDirection: Flickable.AutoFlickIfNeeded
        snapMode: ListView.SnapToItem
        clip: true

        highlightMoveDuration: 100
        highlightRangeMode: ListView.ApplyRange
        preferredHighlightBegin: Metrics.tabStrip
        preferredHighlightEnd: width - Metrics.tabStrip


        MouseArea {
            anchors.fill: parent

            // Scroll the view without the need for a modifier.
            onWheel: function(evt) {
                if(parent.contentWidth < parent.width) {
                    return
                }

                if (evt.angleDelta.y > 0) {
                    parent.contentX = Math.max(0, parent.contentX - 10)
                } else {
                    parent.contentX = Math.min(
                        parent.contentWidth - parent.width,
                        parent.contentX + 10
                    )
                }
            }

            // Ignore all other events and thus pass then  to the
            // underlying ListView.
            onClicked: (mouse) => mouse.accepted = false
            onPressed: (mouse) => mouse.accepted = false
            onReleased: (mouse) => mouse.accepted = false
            onDoubleClicked: (mouse) => mouse.accepted = false
            onPositionChanged: (mouse) => mouse.accepted = false
            onPressAndHold: (mouse) => mouse.accepted = false
        }
    }

    background: Rectangle {
        implicitWidth: Metrics.controlHeight * 8
        implicitHeight: Metrics.tabStrip
        color: Theme.bgAlt
    }
}