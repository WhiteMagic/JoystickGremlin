// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Controls
import Kobold.Foundation


ColumnLayout {
    id: root

    required property DescriptionModel action

    RowLayout {
        spacing: Metrics.gapM

        Label {
            text: "Description"
        }

        TextField {
            Layout.fillWidth: true

            placeholderText: "Enter description"
            text: root.action.description
            selectByMouse: true

            onTextChanged: { root.action.description = text }
        }
    }
}
