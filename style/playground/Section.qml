// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only
//
// Playground-only: a titled section wrapping one control's state swatches.

import QtQuick
import QtQuick.Layouts
import Kobold.Foundation

ColumnLayout {
    id: root

    property string title
    default property alias content: _body.data

    Layout.fillWidth: true
    spacing: Metrics.gapM

    Text {
        text: root.title
        color: Theme.fg
        font.family: FontType.sans
        font.pixelSize: Metrics.textBody
        font.weight: FontType.semiBold
    }

    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: Metrics.hairline
        color: Theme.line
    }

    RowLayout {
        id: _body
        spacing: Metrics.gapL
    }
}
