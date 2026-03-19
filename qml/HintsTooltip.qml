// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Style
import "helpers.js" as Helpers

Popup {
    id: _tooltip

    // Pass in a JS array of objects: { type: int, message: string }
    required property var hints

    readonly property int maxWidth: 400
    readonly property int iconSize: 16

    implicitWidth: maxWidth
    implicitHeight: _content.implicitHeight + 2 * padding

    background: Rectangle {
        color: Universal.chromeMediumLowColor
        border.color: Universal.chromeHighColor
        border.width: 1
    }

    contentItem: ColumnLayout {
        id: _content

        spacing: 8

        Repeater {
            model: _tooltip.hints

            onModelChanged: {
                implicitWidth:  Math.min(_content.implicitWidth, maxWidth)
                implicitHeight: _content.implicitHeight + 2 * padding
            }

            delegate: RowLayout {
                spacing: 8
                Layout.fillWidth: true

                Text {
                    Layout.alignment: Qt.AlignTop
                    Layout.preferredWidth: _tooltip.iconSize
                    Layout.topMargin: 4
                    Layout.rightMargin: 10

                    text: Helpers.hintIcon(modelData.type)
                    color: Helpers.hintColor(modelData.type)

                    font.family: "bootstrap-icons"
                    font.pixelSize: _tooltip.iconSize
                    font.bold: true
                }

                JGText {
                    Layout.fillWidth:  true

                    text: modelData.message ?? ""
                    wrapMode: Text.WordWrap
                }
            }
        }
    }
}
