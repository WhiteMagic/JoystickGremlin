// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Kobold.Controls
import Kobold.Foundation

// Header indicating a child action group within an aciton. Allows adding new actions
// to the slot's group.
Item {
    id: root

    property string label: ""
    property var actionNames: []

    signal actionRequested(string name)

    implicitHeight: Metrics.controlHeight

    RowLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        spacing: Metrics.gapM

        Label {
            text: root.label
            color: Theme.fgMuted
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
