// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Layouts

import Kobold.Foundation

// Visual guide to the left of action rows, visualizing indentation levels similar to
// a file system tree. The guide is only shown for actions that have children and for
// all but the inner-most level. The guide line itself is aligned with the collapse /
// expand icon of the action.
RowLayout {
    id: root

    property bool hasChildren: false
    default property alias content: _content.data

    spacing: 0

    Item {
        Layout.preferredWidth: Metrics.indent
        Layout.fillHeight: true

        Rectangle {
            width: Metrics.hairline
            height: parent.height
            anchors.horizontalCenter: parent.horizontalCenter
            color: root.hasChildren ? Theme.line : "transparent"
        }
    }

    ColumnLayout {
        id: _content

        Layout.fillWidth: true
        Layout.topMargin: Metrics.gapM - Metrics.actionRowInset
        spacing: Metrics.gapM
    }
}
