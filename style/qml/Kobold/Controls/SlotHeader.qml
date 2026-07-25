// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Layouts
import Kobold.Foundation

// SPEC §8 slot header (24px): scaffolding, not content. The only thing that says "actions
// live below me." Accent is never used here -- it would repeat per slot.
Item {
    id: root

    property string label: ""
    property var actionNames: []

    signal actionRequested(string name)

    implicitHeight: Metrics.ctrlH

    RowLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        spacing: Metrics.gapM

        Text {
            text: root.label
            color: Theme.fgMuted
            font.family: FontType.sans
            font.pixelSize: Metrics.textDetail
        }

        Rectangle {
            Layout.fillWidth: true
            height: Metrics.hairline
            color: Theme.line
        }

        AddActionMenuButton {
            variant: "ghost"
            model: root.actionNames
            onActionRequested: (name) => root.actionRequested(name)
        }
    }
}
