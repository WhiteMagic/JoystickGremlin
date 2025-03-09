// -*- coding: utf-8; -*-
//
// Copyright (C) 2019 Lionel Ott
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
    width: 1400
    height: 900
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
                    if(fpath === "")
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

                ToolTip {
                    visible: parent.hovered
                    text: qsTr("Create new profile")
                    delay: 500
                }

                onClicked: {
                    backend.newProfile()
                }
            }
            ToolButton {
                icon.source: "qrc:///icons/profile_save"

                ToolTip {
                    visible: parent.hovered
                    text: qsTr("Save current profile")
                    delay: 500
                }

                onClicked: {
                    var fpath = backend.profilePath()
                    if(fpath === "")
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

                ToolTip {
                    visible: parent.hovered
                    text: qsTr("Load profile")
                    delay: 500
                }

                onClicked: {
                    idLoadProfileFileDialog.open()
                }
            }
            ToolButton {
                icon.source: "qrc:///icons/activate"
                icon.color: backend.gremlinActive ? "green" : "black"

                ToolTip {
                    visible: parent.hovered
                    text: qsTr("Toggle Gremlin")
                    delay: 500
                }

                onClicked: {
                    backend.toggleActiveState()
                }
            }
            ToolButton {
                icon.source: "qrc:///icons/options"

                ToolTip {
                    visible: parent.hovered
                    text: qsTr("Open options dialog")
                    delay: 500
                }

                onClicked: {
                    Helpers.createComponent("DialogOptions.qml")
                }
            }

            ToolButton {
                text: bsi.icons.chart
                font.family: "bootstrap-icons"
                font.pixelSize: 20
                font.weight: 900

                ToolTip {
                    visible: parent.hovered
                    text: qsTr("Open input viewer")
                    delay: 500
                }

                onClicked: {
                    Helpers.createComponent("DialogInputViewer.qml")
                }
            }

            Rectangle {
                Layout.fillWidth: true
            }

            Switch {
                text: "Dark Mode"

                ToolTip {
                    visible: parent.hovered
                    text: qsTr("Toggle dark mode")
                    delay: 500
                }

                onToggled: function() {
                    _root.Universal.theme = position ? Universal.Dark : Universal.Light;
                }
            }

            ComboBox {
                id: _modeSelector
                model: _toolbar.modes.modeList
                textRole: "name"

                ToolTip {
                    visible: parent.hovered
                    text: qsTr("Select mode to edit")
                    delay: 500
                }

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

        // Forces a full refresh of the UI
        function onReloadUi() {
            let currentDeviceIndex = _devicePanel.currentIndex
            _deviceModel.modelReset()
            _deviceListModel.modelReset()
            _inputConfigurationPanel.reload()
            _devicePanel.currentIndex = currentDeviceIndex
        }

        // Updates a single input item button
        function onInputItemChanged(index) {
            _deviceModel.refreshInput(index)
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

        function onProfileChanged() {
            _scriptManager.scriptModel = Qt.binding(() => backend.scriptModel)
        }
    }

    function showIntermediateOutput(state)
    {
        // Show the appropriate input list
        _ioDeviceList.visible = state
        _deviceInputList.visible = !state
        _inputConfigurationPanel.visible = true

        // Hide the plugin manager
        _scriptManager.visible = false
        _btnPluginManager.checked = false

        // Ensure the actions for the active input are shown
        if(state)
        {
            _inputConfigurationPanel.inputIndex = _ioDeviceList.inputIndex
            _inputConfigurationPanel.inputIdentifier =
                _ioDeviceList.inputIdentifier
        }
        else
        {
            _inputConfigurationPanel.inputIndex = _deviceInputList.inputIndex
            _inputConfigurationPanel.inputIdentifier =
                _deviceInputList.inputIdentifier
        }
    }

    function showScriptManager()
    {
        // Show the appropriate input list
        _ioDeviceList.visible = false
        _deviceInputList.visible = false
        _deviceInputList.visible = false
        _ioDeviceList.visible = false
        _inputConfigurationPanel.visible = false

        _scriptManager.visible = true
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

                Layout.minimumHeight: 50
                Layout.maximumHeight: 50
                Layout.fillWidth: true

                deviceListModel: _deviceListModel

                // Trigger a model update on the DeviceInputList
                onDeviceGuidChanged: function()
                {
                    _deviceModel.guid = deviceGuid
                }

                Component.onCompleted: {
                    // Ensure the physical input panel is shown and the first
                    // device is highlighted
                    currentIndex = 0
                    showIntermediateOutput(false)
                }
            }

            JGTabButton {
                id: _btnPluginManager

                text: "Scripts"

                onClicked: () => {
                    showScriptManager()
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

            clip: true
            orientation: Qt.Horizontal

            // List of the inputs of the currently selected device
            DeviceInputList {
                id: _deviceInputList

                visible: true
                SplitView.minimumWidth: 200

                device: _deviceModel

                // Trigger a model update on the InputConfiguration
                onInputIdentifierChanged: {
                    _inputConfigurationPanel.inputIndex = inputIndex
                    _inputConfigurationPanel.inputIdentifier = inputIdentifier
                }
            }

            // List of the inputs of the intermediate output device
            IntermediateOutputDevice {
                id: _ioDeviceList

                visible: false
                SplitView.minimumWidth: 200

                device: backend.getIODeviceManagementModel()

                // Trigger a model update on the InputConfiguration
                onInputIdentifierChanged: {
                    _inputConfigurationPanel.inputIndex = inputIndex
                    _inputConfigurationPanel.inputIdentifier = inputIdentifier
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

        ScriptManager {
            id: _scriptManager

            Layout.fillHeight: true
            Layout.fillWidth: true
            // Without this the height bugs out
            Layout.verticalStretchFactor: 10

            visible: false
        }
    }

} // ApplicationWindow