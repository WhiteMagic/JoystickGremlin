// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts

import Gremlin.Config
import Gremlin.Util
import Kobold.Controls

Item {
    ProfileAutoLoadingModel {
        id: _model
    }

    FileDialog {
        id: _profileFileDialog

        property var associatedField

        nameFilters: ["Profile files (*.xml)"]
        title: "Select a File"

        onAccepted: () => {
            associatedField.text =
                selectedFile.toString().substring("file:///".length)
        }
    }

    FileDialog {
        id: _executableFileDialog

        property var associatedField

        nameFilters: ["Executable files (*.exe)"]
        title: "Select an Executable"

        onAccepted: () => {
            associatedField.text =
                selectedFile.toString().substring("file:///".length)
        }
    }

    Dialog {
        id: _executableSelectorDialog

        property int selectedIndex: -1
        property string selectedValue: ""
        property var associatedField

        title: "Select Executable"
        standardButtons: Dialog.Ok | Dialog.Cancel
        modal: true

        parent: Overlay.overlay
        anchors.centerIn: parent
        width: parent.width * 0.8
        height: parent.height * 0.8

        ColumnLayout {
            id: _dialogContent

            anchors.fill: parent

            ScrollList {
                id: _processListViee

                Layout.fillWidth: true
                Layout.fillHeight: true

                spacing: Metrics.gapS

                model: ProcessListModel {}

                delegate: Button {
                    width: ListView.view.width

                    contentItem: Label {
                        text: model.display
                        horizontalAlignment: Text.AlignLeft
                    }

                    highlighted: index === _executableSelectorDialog.selectedIndex

                    onClicked: () => {
                        _executableSelectorDialog.selectedIndex = index
                        _executableSelectorDialog.selectedValue = model.display
                    }
                }
            }
        }

        onAccepted: () => {
            if (selectedIndex != -1) {
                associatedField.text = selectedValue
            }
        }

        onAboutToShow: () => {
            _processListViee.model.refresh()
        }
    }

    implicitHeight: _content.implicitHeight
    implicitWidth: _content.implicitWidth

    ColumnLayout {
        id: _content
        anchors.fill: parent

        Repeater {
            model: _model

            delegate: AutoLoadEntry {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignRight

                profile: model.profile
                executable: model.executable
                isEnabled: model.isEnabled
            }
        }

        Button {
            Layout.alignment: Qt.AlignCenter

            text: "New Entry"

            onClicked: () => { _model.newEntry() }
        }
    }

    component AutoLoadEntry : Item {
        property alias profile: _profile.text
        property alias executable: _executable.text
        property alias isEnabled: _isEnabled.checked

        implicitHeight: _item.implicitHeight

        ColumnLayout {
            id: _item

            anchors.fill: parent

            // Buttons to select the profile and executable file for the entry
            // as well as enable/disable the entry and delete it.
            RowLayout {
                Button {
                    text: "Select Profile"
                    onClicked: () => {
                        _profileFileDialog.associatedField = _profile
                        _profileFileDialog.open()
                    }
                }

                Button {
                    text: "Browse Executable"
                    onClicked: () => {
                        _executableFileDialog.associatedField = _executable
                        _executableFileDialog.open()
                    }
                }

                Button {
                    text: "Select Executable"

                    onClicked: () => {
                        _executableSelectorDialog.associatedField = _executable
                        _executableSelectorDialog.open()
                    }
                }

                Spacer {}

                Switch {
                    id: _isEnabled

                    text: checked ? "On" : "Off"

                    onToggled: () => { model.isEnabled = checked }
                }

                ToolButton {
                    icon.name: "delete"

                    onClicked: () => { _model.removeEntry(index) }
                }

            }

            TextField {
                id: _profile

                Layout.fillWidth: true

                readOnly: true
                onTextChanged: () => { model.profile = text }
            }

            // Executable path field with button to enable editing to support
            // usage of regular expressions.
            RowLayout {
                TextField {
                    id: _executable

                    Layout.fillWidth: true

                    readOnly: true
                    onTextChanged: () => { model.executable = text }
                }
                ToolButton {
                    icon.name: "edit"

                    checkable: true

                    onToggled: () => { _executable.readOnly = !checked }
                }
            }

            Spacer {
                Layout.preferredHeight: 10
            }
        }
    }
}
