// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Config
import Gremlin.Device
import Gremlin.Profile
import Gremlin.UI
import Kobold.Controls
import Kobold.Foundation
import Kobold.Views
import "helpers.js" as Helpers

ApplicationWindow {

    // Basic application setup.
    title: backend.windowTitle
    minimumWidth: Metrics.dp(1300)
    minimumHeight: Metrics.dp(700)
    visible: true
    color: Theme.bg
    id: _root

    Component.onCompleted: () => {
        _restoringGeometry = false
    }

    // The only application termination path, use by both standard UI interaction as
    // well as the system tray.
    function quitGremlin() {
        if (backend.profileContainsUnsavedChanges) {
            _saveBeforeQuitDialog.open()
        } else {
            Qt.quit()
        }
    }

    // Customize dimensions combined menu and toolbar.
    readonly property int _headerControlSize: Metrics.dp(28)
    readonly property int _headerIconSize: Metrics.dp(18)

    property var _geom: backend.windowGeometry(
        "main-window-geometry", Metrics.windowWidth, Metrics.windowHeight,
        minimumWidth, minimumHeight
    )

    // Prevent startup overwriting persisted geometry information.
    property bool _restoringGeometry: true

    x: _geom.x
    y: _geom.y
    width: _geom.width
    height: _geom.height

    // Persists window geometry after a short delay to save once changes stop.
    Timer {
        id: _geometrySaveTimer
        interval: 500
        repeat: false

        onTriggered: () => {
            _geom.save(_root.x, _root.y, _root.width, _root.height)
        }
    }

    onXChanged: if (!_restoringGeometry) _geometrySaveTimer.restart()
    onYChanged: if (!_restoringGeometry) _geometrySaveTimer.restart()
    onWidthChanged: if (!_restoringGeometry) _geometrySaveTimer.restart()
    onHeightChanged: if (!_restoringGeometry) _geometrySaveTimer.restart()

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

    // Single merged menu bar, toolbar, and mode selector.
    header: ToolBar {
        id: _toolbar

        RowLayout {
            anchors.fill: parent

            MenuBar {
                id: _menuBar

                Layout.fillHeight: true

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
                    Menu {
                        title: qsTr("Recent")

                        width: {
                            let result = 0
                            let padding = 0
                            for (let i = 0; i < count; ++i) {
                                let item = itemAt(i)
                                result = Math.max(item.contentItem.implicitWidth, result)
                                padding = Math.max(item.padding, padding)
                            }
                            return result + padding * 2
                        }

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
                            Helpers.createComponent("DialogManageModes.qml", _root)
                        }
                    }
                    MenuItem {
                        text: qsTr("Input Viewer")
                        onTriggered: () => {
                            Helpers.createComponent("DialogInputViewer.qml", _root, {})
                        }
                    }
                    MenuItem {
                        text: qsTr("Calibration")
                        onTriggered: () => {
                            Helpers.createComponent("DialogCalibration.qml", _root)
                        }
                    }
                    MenuItem {
                        text: qsTr("Device Information")
                        onTriggered: () => {
                            Helpers.createComponent("DialogDeviceInformation.qml", _root)
                        }
                    }
                    MenuSeparator {}
                    MenuItem {
                        text: qsTr("Auto Mapper")
                        onTriggered: () => {
                            Helpers.createComponent("DialogAutoMapper.qml", _root)
                        }
                    }
                    MenuItem {
                        text: qsTr("Swap Devices")
                        onTriggered: () => {
                            Helpers.createComponent("DialogSwapDevices.qml", _root)
                        }
                    }
                    MenuSeparator {}
                    MenuItem {
                        text: qsTr("Options")
                        onTriggered: () => {
                            Helpers.createComponent("DialogOptions.qml", _root)
                        }
                    }
                }

                // Help menu.
                Menu {
                    title: qsTr("Help")

                    MenuItem {
                        text: qsTr("About")
                        onTriggered: () => {
                            Helpers.createComponent("DialogAbout.qml", _root)
                        }
                    }
                }
            }

            Item {
                Layout.preferredWidth: Metrics.gapL * 2
            }

            // Toolbar section.
            ToolButton {
                icon.name: "new_profile"
                controlSize: _root._headerControlSize
                iconSize: _root._headerIconSize
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: qsTr("Create new profile")

                onClicked: () => { backend.newProfile() }
            }
            ToolButton {
                icon.name: "save_profile"
                controlSize: _root._headerControlSize
                iconSize: _root._headerIconSize
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
                controlSize: _root._headerControlSize
                iconSize: _root._headerIconSize
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: qsTr("Load profile")

                onClicked: () => { _loadProfileFileDialog.open() }
            }
            ToolButton {
                icon.name: "input_viewer"
                controlSize: _root._headerControlSize
                iconSize: _root._headerIconSize
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: qsTr("Open input viewer")

                onClicked: () => {
                    Helpers.createComponent("DialogInputViewer.qml", _root, {})
                }
            }
            ToolButton {
                icon.name: "options"
                controlSize: _root._headerControlSize
                iconSize: _root._headerIconSize
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: qsTr("Open options")

                onClicked: () => {
                    Helpers.createComponent("DialogOptions.qml", _root)
                }
            }
            Item {
                Layout.preferredWidth: Metrics.gapM
            }
            ToolButton {
                icon.name: "activate"
                iconRole: backend.gremlinActive ? "accent" : "fg"
                controlSize: _root._headerControlSize
                iconSize: _root._headerIconSize
                ToolTip.visible: hovered
                ToolTip.delay: 500
                ToolTip.text: qsTr("Toggle Gremlin")

                onClicked: () => { backend.toggleActiveState() }
            }

            Spacer {}

            // Mode selector drop down selection.
            Label {
                Layout.rightMargin: Metrics.gapM

                text: "Configuring mode"
            }

            ComboBox {
                id: _modeSelector

                Layout.preferredWidth: Metrics.labelColumn
                Layout.rightMargin: Metrics.gapM

                model: ModeListModel {}
                textRole: "name"
                valueRole: "name"

                onActivated: () => { uiState.setCurrentMode(currentText) }

                Component.onCompleted: () => {
                    currentIndex = find(uiState.currentMode)
                }
            }
        }
    }

    // Footer showing status and the active as well as editing mode.
    footer: Rectangle {
        id: _footer

        implicitHeight: Metrics.menuFooterHeight
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

                Label {
                    text: qsTr("Status:")
                    color: Theme.fgMuted
                    font.pixelSize: Metrics.textDetail
                }
                Label {
                    text: Helpers.selectText(
                            backend.gremlinActive, qsTr("Active"), qsTr("Not Running")
                        ) +
                        Helpers.selectText(
                            backend.gremlinActive & backend.gremlinPaused, qsTr(" (Paused)"), ""
                        )
                    font.pixelSize: Metrics.textDetail
                    font.weight: FontType.semiBold
                }
            }

            Row {
                spacing: Metrics.gapS

                Label {
                    text: qsTr("Executing:")
                    color: Theme.fgMuted
                    font.pixelSize: Metrics.textDetail
                }
                Label {
                    text: backend.currentMode
                    font.pixelSize: Metrics.textDetail
                    font.weight: FontType.semiBold
                }
            }

            Row {
                spacing: Metrics.gapS
                Layout.fillWidth: true

                Label {
                    text: qsTr("Editing:")
                    color: Theme.fgMuted
                    font.pixelSize: Metrics.textDetail
                }
                Label {
                    text: uiState.currentMode
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

        Divider {
            Layout.fillWidth: true
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: false

            implicitHeight: _tabStripRow.implicitHeight

            // Visually connect the input selection, device, and toolbar.
            Rectangle {
                anchors.fill: parent
                color: Theme.bgAlt
            }

            RowLayout {
                id: _tabStripRow

                anchors.fill: parent
                spacing: 0

                ToolButton {
                    icon.name: "tab_left"
                    Layout.fillHeight: true
                    Layout.preferredWidth: Metrics.controlHeight

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
                    Layout.preferredWidth: Metrics.controlHeight

                    enabled: _deviceList.canScrollForward

                    onClicked: () => { _deviceList.nextTab() }
                }

                Rectangle {
                    Layout.preferredWidth: Metrics.hairline
                    Layout.fillHeight: true
                    Layout.margins: Metrics.gapS

                    color: Theme.line
                }

                // Scripts and settings tabs.
                DeviceTabBar {
                    Component.onCompleted: () => { _scriptButton.checked = false }

                    TabButton {
                        id: _scriptButton

                        text: "Scripts"
                        width: Metrics.paddedTabButtonWidth(_metricScripts.width)
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
                        width: Metrics.paddedTabButtonWidth(_metricProfileSettings.width)
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

        // Separates the device seletion bar from the panels below.
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: Metrics.hairline

            color: Theme.line
        }

        // Main UI which contains the active device's inputs on the left and actions
        // assigned to the currently selected input on the right.
        SplitView {
            id: _splitView

            // Ensure the widget covers the entire remaining area in the window.
            Layout.fillHeight: true
            Layout.fillWidth: true

            clip: true
            orientation: Qt.Horizontal

            // List currently selected joystick device inputs (left panel).
            DeviceInputList {
                id: _deviceInputList

                visible: uiState.currentTab === "physical"
                SplitView.minimumWidth: Metrics.leftPaneMin

                device: _deviceModel
            }

            // List logical device inputs (left panel).
            LogicalDevice {
                id: _logicalDeviceList

                visible: uiState.currentTab === "logical"
                SplitView.minimumWidth: Metrics.leftPaneMin

                // Trigger a model update on the InputConfiguration.
                onInputIdentifierChanged: () => {
                    uiState.setCurrentInput(inputIdentifier, inputIndex)
                }
            }

            // List keyboard inputs (left panel).
            KeyboardInputList {
                id: _keyboardInputList

                visible: uiState.currentTab === "keyboard"
                SplitView.minimumWidth: Metrics.leftPaneMin
            }

            // List of the actions associated with the currently selected
            // input (right panel).
            InputConfiguration {
                id: _inputConfigurationPanel

                SplitView.fillWidth: true
                SplitView.fillHeight: true
                SplitView.minimumWidth: Metrics.rightPaneMin

                visible: !["scripts", "settings"].includes(uiState.currentTab)

                Component.onCompleted: () => {
                    inputItemModel = backend.getInputItem(
                        uiState.currentInput,
                        uiState.currentInputIndex
                    )
                }
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
