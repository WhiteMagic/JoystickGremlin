// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kobold.Foundation

// Public plugin-facing kit component: the source row for a multi-input action (SPEC:
// Merge Axis, Dual Axis Deadzone). A label showing the assigned input -- or, when
// unassigned, its instruction as the value itself (isAssigned: false), not hidden -- plus
// a separate "Assign" push button as the click target.
Item {
    id: root

    required property string valueLabel
    property bool isAssigned: true

    signal clicked()

    implicitHeight: Metrics.controlHeight
    implicitWidth: _row.implicitWidth

    RowLayout {
        id: _row

        anchors.fill: parent
        spacing: Metrics.gapM

        Text {
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: root.valueLabel
            color: root.isAssigned ? Theme.fg : Theme.fgDisabled
            font.family: FontType.sans
            font.pixelSize: Metrics.textBody
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        ToolButton {
            icon.name: "assign"
            onClicked: root.clicked()
        }
    }
}
