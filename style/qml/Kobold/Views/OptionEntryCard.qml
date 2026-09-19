// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Config
import Kobold.Controls
import Kobold.Foundation
import "helpers.js" as Helpers

ColumnLayout {
    id: root

    property string title: "No title"
    property string explanation: "No description"
    default property alias optionElement: _optionElementContainer.data

    spacing: Metrics.gapS
    Layout.bottomMargin: Metrics.gapL
    Layout.leftMargin: Metrics.gapL
    Layout.rightMargin: Metrics.gapL

    RowLayout {
        id: _headerRow

        Layout.fillWidth: true
        spacing: Metrics.gapL

        Label {
            Layout.preferredWidth: Metrics.labelColumn
            Layout.fillHeight: true

            text: root.title
        }

        Item {
            Layout.alignment: Qt.AlignVCenter
            Layout.fillWidth: true
            Layout.preferredHeight: _optionElementContainer.implicitHeight

            ColumnLayout {
                id: _optionElementContainer

                anchors.left: parent.left
                anchors.right: parent.right
            }
        }
    }

    Label {
        Layout.fillWidth: true

        text: root.explanation

        color: Theme.fgMuted
        font.pixelSize: Metrics.textDetail
        wrapMode: Text.WordWrap
    }
}
