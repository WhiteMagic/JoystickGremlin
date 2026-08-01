// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

import Kobold.Foundation

ApplicationWindow {
    id: mainWindow
    width: Metrics.dialogWidthM
    height: Metrics.dialogHeightS
    visible: true
    title: qsTr("Joystick Gremlin")

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.gapL

        Label {
            Layout.fillWidth: true

            text: "An error occurred during startup:"

            font.bold: true
            font.pixelSize: Metrics.textBody
        }

        TextArea {
            Layout.fillWidth: true
            Layout.fillHeight: true

            text: errorString
            selectByMouse: true
            font.family: "Consolas"
            wrapMode: Text.WordWrap

            readOnly: true
        }

        Button {
            Layout.alignment: Qt.AlignBottom | Qt.AlignHCenter
            Layout.preferredWidth: 100

            text: qsTr("Ok")

            onClicked: () => { Qt.quit() }
        }
    }

}
