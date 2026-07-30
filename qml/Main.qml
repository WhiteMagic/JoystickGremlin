// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
// Qualified import: an unqualified "QtQuick.Controls.Universal" would
// redeclare MenuBar/TabButton/ComboBox/etc. as its own concrete types,
// silently shadowing the Kobold-styled versions of every bare control
// declared in this file (QML's "last import wins" rule for same-named
// types). Only the Universal.theme sync below is actually needed, for
// the still-Universal-styled legacy right pane.
import QtQuick.Controls.Universal as UniversalStyle
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Config
import Gremlin.Device
import Gremlin.Profile
import Gremlin.Style
import Gremlin.UI
import Kobold.Controls
import Kobold.Foundation
import Kobold.Internal

import "helpers.js" as Helpers

ApplicationWindow {

    // Basic application setup.
    title: backend.windowTitle
    minimumWidth: 1300
    minimumHeight: 700
    width: 1400
    height: 900
    visible: true
    id: _root

    Component.onCompleted: () => {
        Style.isDarkMode = backend.useDarkMode
    }

    // The single quit path, used by the File menu and the tray icon alike.
    // Quitting never goes via close(), which the tray turns into a hide.
    function quitGremlin() {
        if (backend.profileContainsUnsavedChanges) {
            _saveBeforeQuitDialog.open()
        } else {
            Qt.quit()
        }
    }

    Universal.theme: Style.theme
    color: Style.background

    ColorInformation {
        id: colorInformation
    }

    ErrorDialog {
        id: _errorDialog

        title: "A fatal error ocurred"
    }

    MessageDialog {
        id: _notificationDialog

        modality: Qt.ApplicationModal
        buttons: MessageDialog.Ok
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
            backend.saveProfile(currentFile)
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
            backend.loadProfile(currentFile)
        }
    }

    HintsTooltip {
        id: _hintsTooltip

        hints: []
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
                onTriggered: () => { _root.quitGremlin() }
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

            ToolButton {
                icon.name: "new_profile"
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: qsTr("Create new profile")

                onClicked: () => { backend.newProfile() }
            }
            ToolButton {
                icon.name: "save_profile"
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: qsTr("Save current profile")

                onClicked: () => {
                    var fpath = backend.profilePath()
                    if(fpath === "") {
                        _saveProfileFileDialog.open()
                    } else {
                        backend.saveProfile(fpath)
                    }
                }
            }
            ToolButton {
                icon.name: "load_profile"
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: qsTr("Load profile")

                onClicked: () => { _loadProfileFileDialog.open() }
            }
            ToolButton {
                icon.name: "activate"
                iconRole: backend.gremlinActive ? "accent" : "fg"
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: qsTr("Toggle Gremlin")

                onClicked: () => { backend.toggleActiveState() }
            }

            ToolButton {
                icon.name: "input_viewer"
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: qsTr("Open input viewer")

                onClicked: () => {
                    Helpers.createComponent("DialogInputViewer.qml")
                }
            }

            ToolButton {
                icon.name: "options"
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: qsTr("Open options")

                onClicked: () => {
                    Helpers.createComponent("DialogOptions.qml")
                }
            }

            Spacer {}

            Label {
                Layout.rightMargin: 10

                text: "Configuring mode"
            }

            ComboBox {
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

    // Plain adjacency readout (SPEC §10): three facts side by side, no
    // divergence warning/icon/tone -- Editing != Executing mode is routine.
    footer: Rectangle {
        id: _footer

        implicitHeight: Metrics.footer
        color: Theme.bg

        Rectangle {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: Metrics.hairline
            color: Theme.line
        }

        RowLayout {
            anchors.fill: parent
            anchors.leftMargin: Metrics.gapM
            anchors.rightMargin: Metrics.gapM
            spacing: Metrics.gapL

            Row {
                spacing: Metrics.gapS

                Text {
                    text: qsTr("Status:")
                    color: Theme.fgMuted
                    font.family: FontType.sans
                    font.pixelSize: Metrics.textDetail
                }
                Text {
                    text: Helpers.selectText(
                            backend.gremlinActive, qsTr("Active"), qsTr("Not Running")
                        ) +
                        Helpers.selectText(
                            backend.gremlinActive & backend.gremlinPaused, qsTr(" (Paused)"), ""
                        )
                    color: Theme.fg
                    font.family: FontType.sans
                    font.pixelSize: Metrics.textDetail
                    font.weight: FontType.semiBold
                }
            }

            Row {
                spacing: Metrics.gapS

                Text {
                    text: qsTr("Editing:")
                    color: Theme.fgMuted
                    font.family: FontType.sans
                    font.pixelSize: Metrics.textDetail
                }
                Text {
                    text: uiState.currentMode
                    color: Theme.fg
                    font.family: FontType.sans
                    font.pixelSize: Metrics.textDetail
                    font.weight: FontType.semiBold
                }
            }

            Row {
                spacing: Metrics.gapS
                Layout.fillWidth: true

                Text {
                    text: qsTr("Executing mode:")
                    color: Theme.fgMuted
                    font.family: FontType.sans
                    font.pixelSize: Metrics.textDetail
                }
                Text {
                    text: backend.currentMode
                    color: Theme.fg
                    font.family: FontType.sans
                    font.pixelSize: Metrics.textDetail
                    font.weight: FontType.semiBold
                }
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
        function onTabChanged() {
            // Deal with the settings and scripts tab.
            _scriptButton.checked = uiState.currentTab === "scripts"
            _profileSettingsButton.checked = uiState.currentTab === "settings"
        }
    }
    Connections {
        target: backend

        function onProfileChanged() {
            // Not used at the moment.
        }

        function onQuitRequested() {
            _root.quitGremlin()
        }
    }
    Connections {
        target: signal

        // Re-apply UI config (e.g. dark mode) live, so toggling it in the
        // options takes effect immediately instead of needing a restart.
        function onConfigChanged() {
            Style.isDarkMode = backend.useDarkMode
        }

        function onShowError(message, details) {
            _errorDialog.text = message
            _errorDialog.detailedText = details
            _errorDialog.open()
        }

        function onShowNotification(title, message) {
            _notificationDialog.title = title
            _notificationDialog.text = message
            _notificationDialog.open()
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
        spacing: 0

        property InputConfiguration inputConfigurationWidget

        Item {
            Layout.fillWidth: true
            // Nested Layouts default fillHeight to true, which would let
            // this row compete with the SplitView below for vertical
            // space and get vertically centered in the leftover gap.
            Layout.fillHeight: false
            implicitHeight: _tabStripRow.implicitHeight

            // Backs the whole strip in bgAlt so the scroll-affordance
            // buttons (transparent at rest) blend with DeviceTabBar's own
            // bgAlt fill instead of showing the window's bg through.
            Rectangle {
                anchors.fill: parent
                color: Theme.bgAlt
            }

            RowLayout {
                id: _tabStripRow

                anchors.fill: parent
                spacing: 0

                // Only active while there are more devices to scroll to in that
                // direction -- these are a scroll affordance, not a selector.
                ToolButton {
                    icon.name: "tab_left"
                    Layout.fillHeight: true
                    Layout.preferredWidth: Metrics.ctrlH

                    enabled: _deviceList.canScrollBackward

                    onClicked: () => { _deviceList.previousTab() }
                }

                // Horizontal list of "tabs" listing all detected devices.
                DeviceList {
                    id: _deviceList

                    Layout.fillHeight: true
                    Layout.fillWidth: true

                    deviceListModel: _deviceListModel
                }

                ToolButton {
                    icon.name: "tab_right"
                    Layout.fillHeight: true
                    Layout.preferredWidth: Metrics.ctrlH

                    enabled: _deviceList.canScrollForward

                    onClicked: () => { _deviceList.nextTab() }
                }

                // Groups the device tabs from Scripts/Settings (SPEC \u00A710); grouping
                // alone carries the meaning -- no greying, no icons on either side.
                Rectangle {
                    Layout.preferredWidth: Metrics.hairline
                    Layout.fillHeight: true
                    Layout.topMargin: Metrics.gapS
                    Layout.bottomMargin: Metrics.gapS
                    Layout.leftMargin: Metrics.gapM
                    Layout.rightMargin: Metrics.gapM

                    color: Theme.line
                }

                DeviceTabBar {
                    Component.onCompleted: () => { _scriptButton.checked = false }

                    TabButton {
                        id: _scriptButton

                        text: "Scripts"
                        width: _metricScripts.width + 50
                        checked: false

                        onClicked: () => { uiState.setCurrentTab("scripts") }

                        TextMetrics {
                            id: _metricScripts

                            font: _scriptButton.font
                            text: _scriptButton.text
                        }
                    }

                    TabButton {
                        id: _profileSettingsButton

                        text: "Settings"
                        width: _metricProfileSettings.width + 50
                        checked: false

                        onClicked: () => { uiState.setCurrentTab("settings") }

                        TextMetrics {
                            id: _metricProfileSettings

                            font: _profileSettingsButton.font
                            text: _profileSettingsButton.text
                        }
                    }
                }
            }
        }

        // Separates the device/Scripts/Settings tab row from the panels below.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: Metrics.hairline

            color: Theme.line
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
                SplitView.minimumWidth: Metrics.leftPaneMin

                device: _deviceModel
            }

            // List of logical device inputs.
            LogicalDevice {
                id: _logicalDeviceList

                visible: uiState.currentTab === "logical"
                SplitView.minimumWidth: Metrics.leftPaneMin

                // Trigger a model update on the InputConfiguration.
                onInputIdentifierChanged: () => {
                    uiState.setCurrentInput(inputIdentifier, inputIndex)
                }
            }

            KeyboardInputList {
                id: _keyboardInputList

                visible: uiState.currentTab === "keyboard"
                SplitView.minimumWidth: Metrics.leftPaneMin
            }

            // List of the actions associated with the currently selected input.
            InputConfiguration {
                id: _inputConfigurationPanel

                visible: !["scripts", "settings"].includes(uiState.currentTab)

                Component.onCompleted: () => {
                    inputItemModel = backend.getInputItem(
                        uiState.currentInput,
                        uiState.currentInputIndex
                    )
                }

                SplitView.fillWidth: true
                SplitView.fillHeight: true
                SplitView.minimumWidth: Metrics.rightPaneMin
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
