// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Config
import Kobold.Controls
import Kobold.Foundation
import "helpers.js" as Helpers

Window {
    id: _optionsDialog

    minimumWidth: Metrics.dp(1200)
    minimumHeight: Metrics.dp(600)

    // Local to this file -- the section-selector column's width, not a shared design concept.
    readonly property int sectionSelectorWidth: Metrics.dp(200)

    color: Theme.bg

    title: "Options"

    onClosing: () => {
        backend.emitConfigChanged()
    }

    ConfigSectionModel {
        id: _sectionModel
    }

    RowLayout {
        id: _root

        anchors.fill: parent

        // Shows the list of all option sections.
        ScrollList {
            id: _sectionSelector

            Layout.preferredWidth: _optionsDialog.sectionSelectorWidth
            Layout.fillHeight: true

            model: _sectionModel
            delegate: ConfigSectionButton {}

            Component.onCompleted: () => { currentItem.clicked() }
        }

        // Shows the contents of the currently selected section.
        ConfigSection {
            id: _configSection

            Layout.fillHeight: true
            Layout.fillWidth: true
        }
    }
}
