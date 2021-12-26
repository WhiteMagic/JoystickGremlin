// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2020 Lionel Ott
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
import QtQuick.Window 
import Qt.labs.platform as Dialogs

import Gremlin.Device

import "helpers.js" as Helpers


ApplicationWindow {

    // Basic application setup
    title: backend.windowTitle
    width: 1000
    height: 680
    visible: true
    id: _root

    Dialogs.MessageDialog {
        id: idErrorDialog
        title: "An error occurred"
        buttons: Dialogs.MessageDialog.Ok

        text: backend.lastError

        onTextChanged: {
            visible = true
        }
    }

    Dialogs.FileDialog {
        id: idSaveProfileFileDialog
        title: "Please choose a file"

        acceptLabel: "Save"
        defaultSuffix: "xml"
        fileMode: Dialogs.FileDialog.SaveFile
        nameFilters: ["Profile files (*.xml)"]

        onAccepted: {
            backend.saveProfile(Helpers.pythonizePath(file))
        }
    }

    Dialogs.FileDialog {
        id: idLoadProfileFileDialog
        title: "Please choose a file"

        acceptLabel: "Open"
        defaultSuffix: "xml"
        fileMode: Dialogs.FileDialog.OpenFile
        nameFilters: ["Profile files (*.xml)"]

        onAccepted: {
            backend.loadProfile(Helpers.pythonizePath(file))
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
        Row {
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

            ComboBox {
                anchors.verticalCenter: parent.verticalCenter

                model: ["Default", "  Alternative"]
            }
        }
    }


    DeviceListModel {
        id: _deviceListModel
    }

    Device {
        id: _deviceModel
    }


    // Trigger an update of the input list when the model's content changes
    Connections {
        target: backend
        function onInputConfigurationChanged() {
            _deviceModel.modelReset()
        }
    }
    Connections {
        target: signal
        function onReloadUi() {
            _deviceModel.modelReset()
            _deviceListModel.modelReset()
            _inputConfigurationPanel.reload()
        }
    }

    // Horizonbtal list of "tabs" listing all detected devices
    DeviceList {
        id: _devicePanel

        z: 1
        height: 50
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top

        deviceListModel: _deviceListModel

        // Trigger a model update on the DeviceInputList
        onDeviceGuidChanged: {
            _deviceModel.guid = deviceGuid
        }
    }

    // Main UI are containing the list of inputs of the active device on
    // the left and the action associated with the currently selected input
    // on the right.
    SplitView {
        id: _contentLayout

        // Ensure the widget covers the entire remaining area in the window
        anchors.top: _devicePanel.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        orientation: Qt.Horizontal

        // List of the inputs of the currently selected device
        DeviceInputList {
            id: _deviceInputList
            device: _deviceModel
            SplitView.minimumWidth: minimumWidth

            // Trigger a model update on the InputConfiguration
            onInputIdentifierChanged: {
                _inputConfigurationPanel.inputItemBindingListModel =
                    backend.getInputItem(inputIdentifier).inputItemBindings
                _inputConfigurationPanel.inputIdentifier = inputIdentifier
            }

            // Ensure initial state of input list and input configuration is
            // synchronized
            Component.onCompleted: {
                inputIdentifier = device.inputIdentifier(inputIndex)
            }
        }

        // List of the actions associated with the currently selected input
        InputConfiguration {
            id: _inputConfigurationPanel

            SplitView.fillWidth: true
            SplitView.minimumWidth: 600
        }
    }

} // ApplicationWindow