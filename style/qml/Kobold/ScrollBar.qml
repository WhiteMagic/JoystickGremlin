// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.ScrollBar {
    id: control

    implicitWidth: Metrics.gapM
    implicitHeight: Metrics.gapM

    contentItem: Rectangle {
        implicitWidth: Metrics.gapS
        implicitHeight: Metrics.gapS
        radius: width / 2
        color: control.pressed ? Theme.fgMuted : Theme.line
    }
}
