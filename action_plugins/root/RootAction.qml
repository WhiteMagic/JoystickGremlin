// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Kobold.Foundation
import Kobold.Composites

// The invisible container holding every top-level action of a binding's sequence -- no
// header, chevron, name field, guide or indent of its own (SPEC §8: "RootAction is
// invisible"; the BindingHeader above this already carries the sequence-level description,
// Add action and remove). Depth 0 has no indent, so children sit flush left with no
// TreeIndent wrapper around the list itself.
ColumnLayout {
    id: root

    required property RootModel action

    spacing: 0

    ActionList {
        Layout.fillWidth: true

        containerOwner: root.action
        containerName: "children"
    }
}
