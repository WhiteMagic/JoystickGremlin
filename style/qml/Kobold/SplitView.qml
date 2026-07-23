// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.SplitView {
    id: control

    // No drag-grip decoration, no shadow (R2) -- a 1px line that reads slightly
    // darker on press, same convention as ScrollBar's handle.
    handle: Rectangle {
        implicitWidth: control.orientation === Qt.Horizontal ? Metrics.hairline : control.width
        implicitHeight: control.orientation === Qt.Horizontal ? control.height : Metrics.hairline
        color: T.SplitHandle.pressed ? Theme.fgMuted : Theme.line
    }
}
