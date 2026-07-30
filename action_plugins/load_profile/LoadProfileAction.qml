// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Controls
import Kobold.Foundation


// Body only -- no chevron, header, name field, guide or indent, those are the core's.
ColumnLayout {
    id: root

    required property LoadProfileModel action

    RowLayout {
        spacing: Metrics.gapM

        Label {
            text: "Profile filename"
        }

        TextField {
            id: _profileFilename

            Layout.fillWidth: true

            placeholderText: "Enter a profile filename"
            text: root.action.profile_filename
            selectByMouse: true

            onTextChanged: { root.action.profile_filename = text }
        }

        Button {
            text: "Select file"

            onClicked: { _fileDialog.open() }
        }
    }

    FileDialog {
        id: _fileDialog

        nameFilters: ["Profile files (*.xml)"]
        title: "Select a file"

        onAccepted: {
            _profileFilename.text = selectedFile.toString().substring("file:///".length)
        }
    }
}
