// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Window

import Gremlin.Util
import Kobold.Foundation

Window {
    minimumWidth: Metrics.dp(600)
    minimumHeight: Metrics.dp(400)

    color: Theme.bg

    title: qsTr("Release Notes")

    ReleaseNotes {
        id: _releaseNotes
    }

    ScrollView {
        id: _pane

        anchors.fill: parent
        contentWidth: availableWidth

        TextEdit {
            width: _pane.availableWidth
            leftPadding: Metrics.gapM
            rightPadding: Metrics.gapM
            topPadding: Metrics.gapS
            bottomPadding: Metrics.gapS

            readOnly: true
            selectByMouse: true
            wrapMode: TextEdit.Wrap
            textFormat: TextEdit.MarkdownText
            text: _releaseNotes.text

            color: Theme.fg
            selectionColor: Theme.bgSelected
            selectedTextColor: Theme.fg
            font.family: FontType.sans
            font.pixelSize: Metrics.textBody

            Component.onCompleted: () => {
                _releaseNotes.format(textDocument, Metrics.gapL * 2, Metrics.gapS)
            }
        }
    }
}
