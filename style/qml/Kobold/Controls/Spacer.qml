// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Layouts

// Expanding filler for a RowLayout or ColumnLayout, picking the fill
// direction from the immediate parent so callers don't have to.
Item {
    Layout.fillWidth: parent instanceof RowLayout
    Layout.fillHeight: parent instanceof ColumnLayout
}
