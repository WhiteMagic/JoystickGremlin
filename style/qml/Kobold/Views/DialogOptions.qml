// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Config
import Gremlin.UI
import Kobold.Controls
import Kobold.Foundation
import "helpers.js" as Helpers

Window {
    id: _optionsDialog

    minimumWidth: Metrics.dp(1200)
    minimumHeight: Metrics.dp(600)

    color: Theme.bg

    title: "Options"

    readonly property ConfigSectionModel _sectionModel:
        ModelFactory.configSectionModel(_optionsDialog)

    onClosing: () => {
        backend.emitConfigChanged()
    }

    RowLayout {
        id: _root

        anchors.fill: parent

        // Shows the list of all option sections.
        Rectangle {
            Layout.preferredWidth: Metrics.labelColumn
            Layout.fillHeight: true

            color: Theme.bgAlt

            ScrollList {
                id: _sectionSelector

                anchors.fill: parent
                anchors.topMargin: Metrics.gapM

                spacing: Metrics.gapS
                scrollbarAlwaysVisible: false

                model: _optionsDialog._sectionModel
                delegate: ConfigSectionButton {}

                footer: Item {
                    width: ListView.view.width
                    height: Metrics.gapM
                }

                Component.onCompleted: () => { currentItem.clicked() }
            }
        }

        // Shows the contents of the currently selected section.
        ConfigSection {
            id: _configSection

            Layout.fillHeight: true
            Layout.fillWidth: true
        }
    }
}
