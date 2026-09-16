// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only
//
// Playground-only: a titled section wrapping one control's state swatches.

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kobold.Foundation

ColumnLayout {
    id: root

    property string title
    default property alias content: _body.data

    Layout.fillWidth: true
    spacing: Metrics.gapM

    Label {
        text: root.title
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
