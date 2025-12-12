// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtWebView

import QtQuick.Controls.Universal

import Gremlin.About

Window {
    minimumWidth: 500
    minimumHeight: 300
    color: Universal.background
    title: qsTr("About")


    ColumnLayout {
        anchors.fill: parent

        DisplayLabel {
            text: "<b>Joystick Gremlin</b>"
            font.pointSize: 36
        }

        DisplayLabel {
            text: "Release 14"
            font.pointSize: 14
        }

        DisplayLabel {
            text: "<html><a href='https://whitemagic.github.io/JoystickGremlin/'>https://whitemagic.github.io/JoystickGremlin/</a></html>"
            font.pointSize: 14
            onLinkActivated: (url) => { Qt.openUrlExternally(url) }
        }
    }

    component DisplayLabel : Label {
        Layout.fillWidth: true
        Layout.alignment: Qt.AlignHCenter
        horizontalAlignment: Text.AlignHCenter
    }
}
