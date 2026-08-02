// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Kobold.Foundation

Window {
    minimumWidth: Metrics.dp(500)
    minimumHeight: Metrics.dp(300)

    color: Theme.bg

    title: qsTr("About")

    ColumnLayout {
        anchors.fill: parent

        DisplayLabel {
            text: "<b>Joystick Gremlin</b>"
            font.pixelSize: Metrics.textBody
        }

        DisplayLabel {
            text: "Release " + backend.gremlinVersion
            font.pixelSize: Metrics.textBody
        }

        DisplayLabel {
            text: "<html><a href='https://whitemagic.github.io/JoystickGremlin/'>https://whitemagic.github.io/JoystickGremlin/</a></html>"
            font.pixelSize: Metrics.textBody
            onLinkActivated: (url) => { Qt.openUrlExternally(url) }
        }
    }

    component DisplayLabel : Label {
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignHCenter
        horizontalAlignment: Text.AlignHCenter
    }
}
