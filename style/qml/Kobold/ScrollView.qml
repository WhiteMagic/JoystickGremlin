// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T

T.ScrollView {
    id: control

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset,
                             implicitContentHeight + topPadding + bottomPadding)

    // Disable mobile device scrolling behaviors.
    Binding {
        target: control.contentItem
        property: "boundsBehavior"
        value: Flickable.StopAtBounds
        restoreMode: Binding.RestoreNone
    }

    Binding {
        target: control.contentItem
        property: "boundsMovement"
        value: Flickable.StopAtBounds
        restoreMode: Binding.RestoreNone
    }

    ScrollBar.vertical: ScrollBar {
        parent: control
        x: control.mirrored ? 0 : control.width - width
        y: control.topPadding
        height: control.availableHeight
        active: control.ScrollBar.horizontal.active
    }

    ScrollBar.horizontal: ScrollBar {
        parent: control
        x: control.leftPadding
        y: control.height - height
        width: control.availableWidth
        active: control.ScrollBar.vertical.active
    }
}
