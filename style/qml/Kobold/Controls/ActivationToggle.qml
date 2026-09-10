// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick.Controls
import QtQuick.Layouts

import Kobold.Foundation

// Button press/release activation control.
RowLayout {
    id: root

    property bool pressChecked: false
    property bool releaseChecked: false

    signal pressCheckedEdited(bool value)
    signal releaseCheckedEdited(bool value)

    spacing: Metrics.gapS

    CheckBox {
        text: "Press"
        checked: root.pressChecked
        onToggled: { root.pressCheckedEdited(checked) }
    }

    CheckBox {
        text: "Release"
        checked: root.releaseChecked
        onToggled: { root.releaseCheckedEdited(checked) }
    }
}
