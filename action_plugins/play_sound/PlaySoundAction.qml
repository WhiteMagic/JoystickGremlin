// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Kobold.Controls
import Kobold.Foundation


ColumnLayout {
    id: root

    required property PlaySoundModel action

    RowLayout {
        spacing: Metrics.gapM

        Label {
            text: "Audio filename"
        }

        TextField {
            id: _soundFilename

            Layout.fillWidth: true

            text: root.action.soundFilename
            placeholderText: "Input the name of the audio file to play"
            selectByMouse: true

            onTextChanged: { root.action.soundFilename = text }
        }

        Button {
            text: "Select file"

            onClicked: { _fileDialog.open() }
        }

        Label {
            text: "Volume"
        }

        SpinBox {
            value: root.action.soundVolume
            from: 0
            to: 100

            onValueModified: { root.action.soundVolume = value }
        }
    }

    FileDialog {
        id: _fileDialog

        nameFilters: ["Audio files (*.wav *.mp3 *.ogg)"]
        title: "Select a file"

        onAccepted: {
            _soundFilename.text = selectedFile.toString().substring("file:///".length)
        }
    }
}
