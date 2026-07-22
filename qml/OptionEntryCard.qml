// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts

import Gremlin.Config
import "helpers.js" as Helpers

Pane {
    id: root

    property string title: "No title"
    property string explanation: "No description"
    default property alias optionElement: _optionElementContainer.data

    padding: 10

    background: Rectangle {
        color: Universal.chromeLowColor
        border.color: Universal.chromeMediumColor
        border.width: 1
        radius: 4
    }

    RowLayout {
        anchors.left: parent.left
        anchors.right: parent.right

        ColumnLayout {
            Layout.alignment: Qt.AlignTop
            Layout.preferredWidth: 400
            Layout.minimumWidth: 400
            Layout.maximumWidth: 400
            Layout.rightMargin: 10

            Label {
                Layout.fillWidth: true

                text: root.title

                font.weight: 600
                wrapMode: Text.WordWrap
            }

            Label {
                Layout.fillWidth: true

                text: root.explanation

                // horizontalAlignment: Text.AlignJustify
                wrapMode: Text.WordWrap
            }
        }

        Item {
            Layout.alignment: Qt.AlignTop
            Layout.topMargin: 5
            Layout.fillWidth: true
            Layout.preferredHeight: _optionElementContainer.implicitHeight

            ColumnLayout {
                id: _optionElementContainer

                anchors.left: parent.left
                anchors.right: parent.right
            }
        }
    }

}
