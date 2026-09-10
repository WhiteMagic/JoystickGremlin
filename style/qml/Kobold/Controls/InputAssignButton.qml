// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Kobold.Foundation

// UI element showing the recorded input as well as the control to start recording.
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

        Label {
            Layout.fillWidth: true
            Layout.fillHeight: true
            text: root.valueLabel
            color: root.isAssigned ? Theme.fg : Theme.fgDisabled
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        ToolButton {
            icon.name: "assign"
            onClicked: root.clicked()
        }
    }
}
