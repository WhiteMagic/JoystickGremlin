// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2024 Lionel Ott
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.


import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Config
import Gremlin.Device
import Gremlin.Profile

import "helpers.js" as Helpers


ApplicationWindow {

    // Basic application setup
    title: backend.windowTitle
    width: 1000
    height: 680
    visible: true
    id: _root

    MessageDialog {
        id: idErrorDialog
        title: "An error occurred"
        buttons: MessageDialog.Ok

        text: backend.lastError

        onTextChanged: {
            visible = true
        }
    }

    FileDialog {
        id: idSaveProfileFileDialog
        title: "Please choose a file"

        acceptLabel: "Save"
        defaultSuffix: "xml"
        fileMode: FileDialog.SaveFile
        nameFilters: ["Profile files (*.xml)"]

        onAccepted: function()
        {
            backend.saveProfile(Helpers.pythonizePath(currentFile))
        }
    }

    FileDialog {
        id: idLoadProfileFileDialog
        title: "Please choose a file"

        acceptLabel: "Open"
        defaultSuffix: "xml"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Profile files (*.xml)"]

        onAccepted: function()
        {
            backend.loadProfile(Helpers.pythonizePath(currentFile))
        }
    }

    // Menu bar with all its entries
    menuBar: MenuBar {
        Menu {
            title: qsTr("File")

            MenuItem {
                text: qsTr("New Profile")
                onTriggered: {
                    backend.newProfile()
                }
            }
            MenuItem {
                text: qsTr("Load Profile")
                onTriggered: {
                    idLoadProfileFileDialog.open()
                }
            }

            AutoSizingMenu {
                title: qsTr("Recent")

                Repeater {
                    model: backend.recentProfiles
                    delegate: MenuItem {
                        text: modelData
                        onTriggered: {
                            backend.loadProfile(modelData)
                        }
                    }
                }
            }

            MenuItem {
                text: qsTr("Save Profile")
                onTriggered: {
                    var fpath = backend.profilePath()
                    if(fpath == "")
                    {
                        idSaveProfileFileDialog.open();
                    }
                    else
                    {
                        backend.saveProfile(fpath)
                    }
                }
            }
            MenuItem {
                text: qsTr("Save Profile As")
                onTriggered: {
                    idSaveProfileFileDialog.open()
                }
            }
            MenuItem {
                text: qsTr("Exit")
                onTriggered: Qt.quit();
            }
        }
        Menu {
            title: qsTr("Tools")

            MenuItem {
                text: qsTr("Manage Modes")
                onTriggered: Helpers.createComponent("DialogManageModes.qml")
            }
            MenuItem {
                text: qsTr("Input Repeater")
                //onTriggered: Helpers.createComponent(".qml")
            }
            MenuItem {
                text: qsTr("Device Information")
                onTriggered: Helpers.createComponent("DialogDeviceInformation.qml")
            }
            MenuItem {
                text: qsTr("Calibration")
                onTriggered: Helpers.createComponent("DialogCalibration.qml")
            }
            MenuItem {
                text: qsTr("Input Viewer")
                onTriggered: Helpers.createComponent("DialogInputViewer.qml")
            }
            MenuSeparator {}
            MenuItem {
                text: qsTr("PDF Cheatsheet")
                onTriggered: Helpers.createComponent("DialogPDFCheatsheet.qml")
            }
            MenuSeparator {}
            MenuItem {
                text: qsTr("Options")
                onTriggered: Helpers.createComponent("DialogOptions.qml")
            }
            MenuItem {
                text: qsTr("Log Display")
                onTriggered: Helpers.createComponent("DialogLogDisplay.qml")
            }
        }

        Menu {
            title: qsTr("Help")

            MenuItem {
                text: qsTr("About")
                onTriggered: Helpers.createComponent("DialogAbout.qml")
            }
        }
    }

    header: ToolBar {
        id: _toolbar

        property ModeHierarchyModel modes : backend.modeHierarchy

        RowLayout {
            anchors.fill: parent

            ToolButton {
                icon.source: "qrc:///icons/profile_new"

                onClicked: {
                    backend.newProfile()
                }
            }
            ToolButton {
                icon.source: "qrc:///icons/profile_save"

                onClicked: {
                    var fpath = backend.profilePath()
                    if(fpath == "")
                    {
                        idSaveProfileFileDialog.open()
                    }
                    else
                    {
                        backend.saveProfile(fpath)
                    }
                }
            }
            ToolButton {
                icon.source: "qrc:///icons/profile_open"

                onClicked: {
                    idLoadProfileFileDialog.open()
                }
            }
            ToolButton {
                icon.source: "qrc:///icons/activate"
                icon.color: backend.gremlinActive ? "green" : "black"

                onClicked: {
                    backend.toggleActiveState()
                }
            }
            ToolButton {
                icon.source: "qrc:///icons/activate"

                onClicked: {
                    Helpers.createComponent("DialogOptions.qml")
                }
            }

            Rectangle {
                Layout.fillWidth: true
            }

            Switch {
                text: "Dark Mode"

                onToggled: function() {
                    _root.Universal.theme = position ? Universal.Dark : Universal.Light;
                }
            }

            ComboBox {
                id: _modeSelector
                model: _toolbar.modes.modeList
                textRole: "name"

                // TODO: Complete this to have modes show hierarchy information
                // delegate: ItemDelegate {
                //     required property var model
                //     required property int index
                //     required property string name
                //     required property int depth
                //
                //     width: _modeSelector.width
                //     contentItem: Text {
                //         text: "  ".repeat(depth) + name
                //
                //         font: _modeSelector.font
                //         elide: Text.ElideRight
                //         verticalAlignment: Text.AlignVCenter
                //     }
                //     highlighted: _modeSelector.highlightedIndex === index
                // }

                onActivated: function(index) {
                    backend.uiMode = textAt(index)
                }

            }
        }
    }

    footer: Rectangle {
        id: _footer

        height: 30
        color: "#e6e6e6"

        RowLayout {
            anchors.fill: parent

            Label {
                Layout.preferredWidth: 200
                padding: 5

                text: "<B>Status: </B>" +
                    Helpers.selectText(
                        backend.gremlinActive, "Active", "Not Running"
                    ) +
                    Helpers.selectText(
                        backend.gremlinActive & backend.gremlinPaused, " (Paused)", ""
                    )
            }

            Label {
                Layout.fillWidth: true
                padding: 5

                text: "<B>Current mode: </B>" + backend.currentMode
            }
        }
    }

    DeviceListModel {
        id: _deviceListModel
    }

    Device {
        id: _deviceModel
    }

    BootstrapIcons {
        id: bsi
        resource: "qrc:///BootstrapIcons"
    }

    Connections {
        target: signal

        function onReloadUi() {
            _deviceModel.modelReset()
            _deviceListModel.modelReset()
            _inputConfigurationPanel.reload()
        }

        // function onReloadCurrentInputItem() {
        //     _inputConfigurationPanel.reload()
        // }
    }

    Connections {
        target: backend

        function onUiModeChanged() {
            _deviceModel.modelReset()
            _inputConfigurationPanel.reload()
        }
    }

    function showIntermediateOutput(state)
    {
        _ioDeviceList.visible = state
        _deviceInputList.visible = !state
    }

    // Main window content
    ColumnLayout {
        id: _columnLayout

        anchors.fill: parent

        property InputConfiguration inputConfigurationWidget

        RowLayout {
            Layout.fillWidth: true

            // Horizontal list of "tabs" listing all detected devices
            DeviceList {
                id: _devicePanel

                Layout.preferredHeight: 50
                Layout.fillWidth: true
                z: 1

                deviceListModel: _deviceListModel

                // Trigger a model update on the DeviceInputList
                onDeviceGuidChanged: function()
                {
                    _deviceModel.guid = deviceGuid

                    // Ensure the input panel is showing the physical device
                    showIntermediateOutput(false)
                }

                MouseArea {
                    anchors.fill: parent
                    propagateComposedEvents: true
                    onClicked: function(mouse)
                    {
                        showIntermediateOutput(false)
                        mouse.accepted = false
                        // Force selection of the previously selected item in
                        // the input list
                        let old_index = _deviceInputList.inputIndex
                        _deviceInputList.currentIndex = 0
                        _deviceInputList.currentIndex = old_index
                    }
                }

            }

            // Intermediate output entry
            Label {
                text: "Intermediate Output"

                leftPadding: 20
                rightPadding: 20
                topPadding: 10
                bottomPadding: 10

                background: Rectangle {
                    color: _ioDeviceList.visible ?
                        Universal.chromeMediumColor : Universal.background
                }

                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        showIntermediateOutput(true)
                        _ioDeviceList.device = backend.getIODeviceManagementModel()
                    }
                }
            }
        }


        // Main UI which contains the active device's inputs on the left and
        // actions assigned to the currently selected input on the right.
        SplitView {
            id: _splitView

            // Ensure the widget covers the entire remaining area in the window
            Layout.fillHeight: true
            Layout.fillWidth: true

            orientation: Qt.Horizontal

            // List of the inputs of the currently selected device
            DeviceInputList {
                id: _deviceInputList

                visible: false
                SplitView.minimumWidth: 150

                device: _deviceModel

                // Trigger a model update on the InputConfiguration
                onInputIdentifierChanged: {
                    _inputConfigurationPanel.inputIdentifier = inputIdentifier
                }

                // Ensure initial state of input list and input configuration is
                // synchronized
                Component.onCompleted: {
                    // FIXME: Where does this inputIndex variable come from?
                    //inputIdentifier = device.inputIdentifier(inputIndex)
                }
            }

            IntermediateOutputDevice {
                id: _ioDeviceList

                visible: true
                SplitView.minimumWidth: 150

                device: backend.getIODeviceManagementModel()

                // Trigger a model update on the InputConfiguration
                onInputIdentifierChanged: {
                    _inputConfigurationPanel.inputIdentifier = inputIdentifier
                }

                // Ensure initial state of input list and input configuration is
                // synchronized
                Component.onCompleted: {
                    // FIXME: Where does this inputIndex variable come from?
                    //inputIdentifier = device.inputIdentifier(inputIndex)
                }
            }

            // List of the actions associated with the currently selected input
            InputConfiguration {
                id: _inputConfigurationPanel

                SplitView.fillWidth: true
                SplitView.fillHeight: true
                SplitView.minimumWidth: 600
            }
        }
    }

} // ApplicationWindow