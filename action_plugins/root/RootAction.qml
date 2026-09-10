// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Kobold.Foundation
import Kobold.Composites


// The invisible container holding every top-level action of a binding's sequence.
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
