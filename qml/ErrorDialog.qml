// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts

import Gremlin.Style

Popup {
    id: root

    property string title: ""
    property string text: ""
    property string detailedText: ""

    signal accepted()
    signal rejected()

    width: 800
    height: 500
    anchors.centerIn: parent

    popupType: Popup.Item
    closePolicy: Popup.NoAutoClose
    modal: true
    dim: false

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10

        Label {
            Layout.fillWidth: true

            text: root.title

            font.bold: true
            font.pixelSize: 16
        }

        Label {
            Layout.fillWidth: true

            text: root.text

            wrapMode: Text.WordWrap
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            // Fix scrollbar behavior.
            ScrollBar.vertical.interactive: true
            ScrollBar.horizontal.interactive: true
            Component.onCompleted: () => {
                contentItem.boundsMovement = Flickable.StopAtBounds
            }

            TextArea {
                Universal.theme: Style.theme

                text: root.detailedText
                selectByMouse: true
                font.family: "Consolas"

                readOnly: true
            }
        }

        Button {
            Layout.alignment: Qt.AlignRight

            text: "OK"

            onClicked: () => { root.close() }
        }
    }
}
