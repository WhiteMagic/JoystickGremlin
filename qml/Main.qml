// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Config
import Gremlin.Device
import Gremlin.Profile
import Gremlin.Style
import Gremlin.UI

import "helpers.js" as Helpers

ApplicationWindow {

    // Basic application setup.
    title: backend.windowTitle
    width: 1400
    height: 900
    visible: true
    id: _root

    Component.onCompleted: () => {
        Style.isDarkMode = backend.useDarkMode
    }
    Universal.theme: Style.theme
    color: Style.background


    MessageDialog {
        id: _errorDialog

        title: "Error"
    }

    MessageDialog {
        id: _saveBeforeQuitDialog

        title: "Save Changes?"
        modality: Qt.ApplicationModal
        buttons: MessageDialog.Save | MessageDialog.Discard | MessageDialog.Cancel

        text: "There are unsaved changes in the current profile, do you want " +
              "to save them before quitting?"

        onButtonClicked: (button, role) => {
            switch (button) {
                case MessageDialog.Save:
                    var fpath = backend.profilePath()
                    if(fpath === "") {
                        console.log("Saving to " + fpath)
                        _saveProfileFileDialog.quitAfterSave = true
                        _saveProfileFileDialog.open()
                    } else {
                        backend.saveProfile(fpath)
                        Qt.quit()
                    }
                    break
                case MessageDialog.Discard:
                    Qt.quit()
                    break
                case MessageDialog.Cancel:
                    break
            }
        }
    }

    FileDialog {
        id: _saveProfileFileDialog
        title: "Please choose a file"

        property bool quitAfterSave: false

        acceptLabel: "Save"
        defaultSuffix: "xml"
        fileMode: FileDialog.SaveFile
        nameFilters: ["Profile files (*.xml)"]

        onAccepted: () => {
            backend.saveProfile(Helpers.pythonizePath(currentFile))
            if (quitAfterSave) {
                Qt.quit()
            }
        }
    }

    FileDialog {
        id: _loadProfileFileDialog
        title: "Please choose a file"

        acceptLabel: "Open"
        defaultSuffix: "xml"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Profile files (*.xml)"]

        onAccepted: () => {
            backend.loadProfile(Helpers.pythonizePath(currentFile))
        }
    }

    // Menu bar with all its entries.
    menuBar: MenuBar {
        Menu {
            title: qsTr("File")

            // File menu.
            MenuItem {
                text: qsTr("New Profile")
                onTriggered: () => { backend.newProfile() }
            }
            MenuItem {
                text: qsTr("Load Profile")
                onTriggered: () => { _loadProfileFileDialog.open() }
            }
            AutoSizingMenu {
                title: qsTr("Recent")

                Repeater {
                    model: backend.recentProfiles
                    delegate: MenuItem {
                        text: modelData
                        onTriggered: () => { backend.loadProfile(modelData) }
                    }
                }
            }
            MenuItem {
                text: qsTr("Save Profile")
                onTriggered: () => {
                    var fpath = backend.profilePath()
                    if(fpath === "") {
                        _saveProfileFileDialog.open();
                    } else {
                        backend.saveProfile(fpath)
                    }
                }
            }
            MenuItem {
                text: qsTr("Save Profile As")
                onTriggered: () => { _saveProfileFileDialog.open() }
            }
            MenuItem {
                text: qsTr("Exit")
                onTriggered: () => {
                    if (backend.profileContainsUnsavedChanges) {
                        _saveBeforeQuitDialog.open()
                    } else {
                        Qt.quit()
                    }
                }
            }
        }

        // Tools menu.
        Menu {
            title: qsTr("Tools")

            MenuItem {
                text: qsTr("Manage Modes")
                onTriggered: () => {
                    Helpers.createComponent("DialogManageModes.qml")
                }
            }
            // MenuItem {
            //     text: qsTr("Input Repeater")
            //     //onTriggered: Helpers.createComponent(".qml")
            // }
            MenuItem {
                text: qsTr("Input Viewer")
                onTriggered: () => {
                    Helpers.createComponent("DialogInputViewer.qml")
                }
            }
            MenuItem {
                text: qsTr("Calibration")
                onTriggered: () => {
                    Helpers.createComponent("DialogCalibration.qml")
                }
            }
            MenuItem {
                text: qsTr("Device Information")
                onTriggered: () => {
                    Helpers.createComponent("DialogDeviceInformation.qml")
                }
            }
            MenuSeparator {}
            MenuItem {
                text: qsTr("Auto Mapper")
                onTriggered: () => {
                    Helpers.createComponent("DialogAutoMapper.qml")
                }
            }
            MenuItem {
                text: qsTr("Swap Devices")
                onTriggered: () => {
                    Helpers.createComponent("DialogSwapDevices.qml")
                }
            }
            MenuSeparator {}
            MenuItem {
                text: qsTr("Options")
                onTriggered: () => {
                    Helpers.createComponent("DialogOptions.qml")
                }
            }
            // MenuItem {
            //     text: qsTr("Log Display")
            //     onTriggered: () => {
            //         Helpers.createComponent("DialogLogDisplay.qml")
            //     }
            // }
        }

        // Help menu.
        Menu {
            title: qsTr("Help")

            MenuItem {
                text: qsTr("About")
                onTriggered: () => {
                    Helpers.createComponent("DialogAbout.qml")
                }
            }
        }
    }

    header: ToolBar {
        id: _toolbar

        RowLayout {
            anchors.fill: parent

            JGToolButton {
                text: "\uF392"
                tooltip: qsTr("Create new profile")

                onClicked: () => { backend.newProfile() }
            }
            JGToolButton {
                text: "\uF356"
                tooltip: qsTr("Save current profile")

                onClicked: () => {
                    var fpath = backend.profilePath()
                    if(fpath === "") {
                        _saveProfileFileDialog.open()
                    } else {
                        backend.saveProfile(fpath)
                    }
                }
            }
            JGToolButton {
                text: "\uF358"
                tooltip: qsTr("Load profile")

                onClicked: () => { _loadProfileFileDialog.open() }
            }
            JGToolButton {
                text: "\uF448"
                color: backend.gremlinActive ? Style.accent : Style.foreground
                tooltip: qsTr("Toggle Gremlin")

                onClicked: () => { backend.toggleActiveState() }
            }

            JGToolButton {
                text: "\uF3F2"
                tooltip: qsTr("Open input viewer")

                onClicked: () => {
                    Helpers.createComponent("DialogInputViewer.qml")
                }
            }

            JGToolButton {
                text: "\uF3E5"
                tooltip: qsTr("Open options")

                onClicked: () => {
                    Helpers.createComponent("DialogOptions.qml")
                }
            }

            LayoutHorizontalSpacer {}

            Label {
                Layout.rightMargin: 10

                text: "Configuring mode"
            }

            JGComboBox {
                id: _modeSelector

                Layout.preferredWidth: 200
                Layout.rightMargin: 10

                model: ModeListModel {}
                textRole: "name"
                valueRole: "name"

                onActivated: () => { uiState.setCurrentMode(currentText) }

                Component.onCompleted: () => {
                    currentIndex = find(uiState.currentMode)
                }

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
                //     contentItem: JGText {
                //         text: "  ".repeat(depth) + name
                //
                //         font: _modeSelector.font
                //         elide: Text.ElideRight
                //         verticalAlignment: Text.AlignVCenter
                //     }
                //     highlighted: _modeSelector.highlightedIndex === index
                // }
            }
        }
    }

    footer: Rectangle {
        id: _footer

        height: 30
        color: Universal.chromeMediumColor

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

                text: "<B>Executing mode: </B>" + backend.currentMode
            }
        }
    }

    DeviceListModel {
        id: _deviceListModel

        deviceType: "input"
    }

    Device {
        id: _deviceModel

        guid: uiState.currentDevice
    }

    BootstrapIcons {
        id: bsi
        resource: "qrc:///BootstrapIcons"
    }

    Connections {
        target: uiState

        function onModeChanged() {
            _deviceModel.setMode(uiState.currentMode)
            _logicalDeviceList.device.setMode(uiState.currentMode)
            _modeSelector.currentIndex = _modeSelector.find(uiState.currentMode)
        }
    }
    Connections {
        target: backend

        function onProfileChanged() {
            _logicalDeviceList.device =
                backend.getLogicalDeviceManagementModel()
        }
    }
    Connections {
        target: signal

        function onShowError(message, details) {
            _errorDialog.text = message
            _errorDialog.detailedText = details
            _errorDialog.open()
        }
    }

    onClosing: (close) => {
        if (backend.profileContainsUnsavedChanges) {
            _saveBeforeQuitDialog.open()
            close.accepted = false
        }
    }

    // Main window content.
    ColumnLayout {
        id: _columnLayout

        anchors.fill: parent

        property InputConfiguration inputConfigurationWidget

        RowLayout {
            Layout.fillWidth: true

            // Horizontal list of "tabs" listing all detected devices.
            DeviceList {
                id: _deviceList

                Layout.minimumHeight: 50
                Layout.maximumHeight: 50
                Layout.fillWidth: true

                deviceListModel: _deviceListModel
            }
        }

        // Main UI which contains the active device's inputs on the left and
        // actions assigned to the currently selected input on the right.
        SplitView {
            id: _splitView

            // Ensure the widget covers the entire remaining area in the window.
            Layout.fillHeight: true
            Layout.fillWidth: true

            clip: true
            orientation: Qt.Horizontal

            // List of the currently selected device's inputs.
            DeviceInputList {
                id: _deviceInputList

                visible: uiState.currentTab === "physical"
                SplitView.minimumWidth: 250

                device: _deviceModel
            }

            // List of logical device inputs.
            LogicalDevice {
                id: _logicalDeviceList

                visible: uiState.currentTab === "logical"
                SplitView.minimumWidth: 250

                // Trigger a model update on the InputConfiguration
                onInputIdentifierChanged: () => {
                    uiState.setCurrentInput(inputIdentifier, inputIndex)
                }
            }

            // List of the actions associated with the currently selected input.
            InputConfiguration {
                id: _inputConfigurationPanel

                visible: !["scripts", "settings"].includes(uiState.currentTab)

                SplitView.fillWidth: true
                SplitView.fillHeight: true
                SplitView.minimumWidth: 600
            }
        }

        ScriptManager {
            id: _scriptManager

            Layout.fillHeight: true
            Layout.fillWidth: true
            // Without this the height bugs out.
            Layout.verticalStretchFactor: 10

            visible: uiState.currentTab === "scripts"

            scriptListModel: backend.scriptListModel
        }

        ProfileSettings {
            id: _profileSettings

            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.verticalStretchFactor: 10

            visible: uiState.currentTab === "settings"

            settingsModel: ProfileSettingsModel {}
        }
    }

}
