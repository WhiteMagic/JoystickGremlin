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

    property var _children: root.action.getActions("children")

    Repeater {
        model: root._children

        delegate: ActionNode {
            required property var modelData
            required property int index

            Layout.fillWidth: true

            action: modelData
            previousSibling: index > 0 ? root._children[index - 1] : null
        }
    }
}
