// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls

// Thin tooltip-forwarding wrapper; icon/background/hover come from the
// active style's ToolButton (Kobold.ToolButton), not overridden here.
ToolButton {
    property alias tooltip: _tooltip.text

    ToolTip {
        id: _tooltip

        visible: parent.hovered
        delay: 500
    }
}
