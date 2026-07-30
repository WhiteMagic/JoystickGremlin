// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Kobold.Controls
import Kobold.Foundation


// Body only -- no chevron, header, name field, guide or indent, those are the core's.
ColumnLayout {
    id: root

    required property RunCommandModel action

    spacing: Metrics.gapS

    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.gapM

        Label {
            id: _executableLabel

            // Aligns with _argumentsLabel below -- within this action only.
            Layout.preferredWidth: Math.max(_executableLabel.implicitWidth, _argumentsLabel.implicitWidth)

            text: "Executable"
        }

        TextField {
            id: _executable

            Layout.fillWidth: true

            text: root.action.executable
            placeholderText: "Path to the program to run"
            selectByMouse: true

            onTextChanged: { root.action.executable = text }
        }

        Button {
            text: "Select file"

            onClicked: { _fileDialog.open() }
        }
    }

    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.gapM

        Label {
            id: _argumentsLabel

            Layout.preferredWidth: Math.max(_executableLabel.implicitWidth, _argumentsLabel.implicitWidth)

            text: "Arguments"
        }

        TextField {
            Layout.fillWidth: true

            text: root.action.arguments
            placeholderText: "Arguments split on spaces; quote values containing spaces"
            selectByMouse: true

            onTextChanged: { root.action.arguments = text }
        }
    }

    FileDialog {
        id: _fileDialog

        nameFilters: ["Executables (*.exe *.bat *.cmd)", "All files (*)"]
        title: "Select an executable"

        onAccepted: {
            _executable.text = selectedFile.toString().substring("file:///".length)
        }
    }
}
