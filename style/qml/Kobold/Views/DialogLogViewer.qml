// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Log
import Kobold.Foundation

Window {
    id: _root

    minimumWidth: Metrics.dp(800)
    minimumHeight: Metrics.dp(400)

    color: Theme.bg

    title: "Log Viewer"

    ColumnLayout {
        anchors.fill: parent

        spacing: 0

        TabBar {
            id: _tabs

            Layout.fillWidth: true

            TabButton {
                text: "System"
                width: implicitWidth
            }
            TabButton {
                text: "User"
                width: implicitWidth
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true

            currentIndex: _tabs.currentIndex

            LogPane {
                loggerName: "system"
            }
            LogPane {
                loggerName: "user"
            }
        }
    }

    component LogPane : ScrollView {
        id: _pane

        property string loggerName

        readonly property Flickable flickable: contentItem
        // Only changed by contentY moves, so growing content keeps following.
        property bool following: true

        rightPadding: ScrollBar.vertical.width
        contentWidth: availableWidth
        ScrollBar.vertical.policy: ScrollBar.AlwaysOn

        background: Rectangle {
            radius: Metrics.radius
            color: Theme.bgAlt
            border.width: Metrics.hairline
            border.color: Theme.line
        }

        function scrollToBottom() {
            flickable.contentY = Math.max(0, flickable.contentHeight - flickable.height)
        }

        Component.onCompleted: () => {
            _text.text = _source.snapshot()
        }

        LogSource {
            id: _source

            loggerName: _pane.loggerName
        }

        Connections {
            target: _source

            function onRecordAppended(text, evictedChars) {
                _text.append(text)
                if (evictedChars > 0) {
                    _text.remove(0, evictedChars)
                }
            }
        }

        Connections {
            target: _pane.flickable

            function onContentYChanged() {
                _pane.following = _pane.flickable.contentY
                    >= _pane.flickable.contentHeight - _pane.flickable.height - 1
            }
            function onContentHeightChanged() {
                if (_pane.following) {
                    _pane.scrollToBottom()
                }
            }
            function onHeightChanged() {
                if (_pane.following) {
                    _pane.scrollToBottom()
                }
            }
        }

        // Not a TextArea, which scrolls the view to its cursor on every relayout.
        TextEdit {
            id: _text

            width: _pane.availableWidth
            leftPadding: Metrics.gapM
            rightPadding: Metrics.gapM
            topPadding: Metrics.gapS
            bottomPadding: Metrics.gapS

            readOnly: true
            selectByMouse: true
            wrapMode: TextEdit.Wrap
            textFormat: TextEdit.PlainText

            color: Theme.fg
            selectionColor: Theme.bgSelected
            selectedTextColor: Theme.fg
            font.family: FontType.mono
            font.pixelSize: Metrics.textBody
        }
    }
}
