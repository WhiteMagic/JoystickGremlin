// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.Label {
    id: control

    color: control.enabled ? Theme.fg : Theme.fgDisabled
    linkColor: Theme.accent

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody
}
