// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2019 Lionel Ott
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


import QtQuick 2.14
import QtQuick.Controls 2.14
import QtQuick.Dialogs 1.3
import QtQuick.Window 2.14

import gremlin.ui.device 1.0

import "helpers.js" as Helpers


ApplicationWindow {

    // Basic application setup
    title: backend.windowTitle
    width: 1000
    height: 680
    visible: true
    id: root

    FileDialog {
        id: idSaveProfileFileDialog
        title: "Please choose a file"
        folder: shortcuts.home
        defaultSuffix: "xml"
        nameFilters: ["Profile files (*.xml)"]
        selectExisting: false

        onAccepted: {
            backend.saveProfile(fileUrl)
        }
    }

    FileDialog {
        id: idLoadProfileFileDialog
        title: "Please choose a file"
        folder: shortcuts.home
        defaultSuffix: "xml"
        nameFilters: ["Profile files (*.xml)"]
        selectExisting: true

        onAccepted: {
            backend.loadProfile(fileUrl)
            console.log("Dodged")
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

            Menu {
                title: qsTr("Recent")
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


    DeviceListModel {
        id: idDeviceListModel
    }

    // List of all detected devices
    DeviceList {
        id: idDevicePanel

        height: 50
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right

        deviceListModel: idDeviceListModel

        // Trigger a model update on the DeviceInputList
        onDeviceGuidChanged: {
            idDeviceInputList.deviceGuid = deviceGuid
        }
    }

    // Device inputs and configuration of a specific input
    SplitView {
        id: idContentLayout

        anchors.top: idDevicePanel.bottom
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        orientation: Qt.Horizontal

        // List all inputs of a single device
        DeviceInputList {
            id: idDeviceInputList
            deviceGuid: idDevicePanel.deviceGuid
            SplitView.minimumWidth: 200

            // Trigger a model update on the InputConfiguration
            onInputIndexChanged: {
                idInputConfigurationPanel.libraryItemListModel =
                    backend.getInputItem(inputIdentifier).libraryItems
            }
        }

        // Configuration of the selected input
        InputConfiguration {
            id: idInputConfigurationPanel
        }
    }

} // ApplicationWindow
