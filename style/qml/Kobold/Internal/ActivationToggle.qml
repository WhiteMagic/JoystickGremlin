// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick.Controls
import QtQuick.Layouts
import Kobold.Foundation

// Press/Release activation checkboxes (SPEC §7: checkbox = on/off). Replaces the legacy
// TriggerMode's CompactSwitch -- switches are deleted app-wide.
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
        onToggled: root.pressCheckedEdited(checked)
    }

    CheckBox {
        text: "Release"
        checked: root.releaseChecked
        onToggled: root.releaseCheckedEdited(checked)
    }
}
