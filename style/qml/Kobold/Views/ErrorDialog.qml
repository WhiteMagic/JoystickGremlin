// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Kobold.Foundation

Popup {
    id: root

    property string title: ""
    property string text: ""
    property string detailedText: ""

    signal accepted()
    signal rejected()

    width: Metrics.dp(800)
    height: Metrics.dp(500)
    anchors.centerIn: parent

    popupType: Popup.Item
    closePolicy: Popup.NoAutoClose
    modal: true
    dim: false

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: Metrics.gapL

        Label {
            Layout.fillWidth: true

            text: root.title

            font.weight: FontType.semiBold
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
                text: root.detailedText
                selectByMouse: true
                font.family: FontType.mono

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
