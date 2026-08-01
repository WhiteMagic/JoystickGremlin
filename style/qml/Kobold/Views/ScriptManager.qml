// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import Qt.labs.qmlmodels

import Gremlin.Script
import Kobold.Controls
import Kobold.Foundation

import "helpers.js" as Helpers


Item {
    id: _root

    property ScriptListModel scriptListModel : backend.scriptListModel

    // Dialog to select a script to add
    FileDialog {
        id: _selectScript

        title: "Please select a file"

        acceptLabel: "Load"
        defaultSuffix: "py"
        fileMode: FileDialog.OpenFile
        nameFilters: ["Script files (*.py)"]

        onAccepted: function()
        {
            scriptListModel.addScript(selectedFile)
        }
    }

    // Dialog to rename a script
    TextInputDialog {
        id: _renameScriptDialog

        visible: false
        width: Metrics.dialogWidthXS

        property var callback: null

        onAccepted: function(value)
        {
            callback(value)
            visible = false
        }
    }

    SplitView {
        anchors.fill: parent
        anchors.leftMargin: 10

        ColumnLayout {
            SplitView.fillHeight: true
            SplitView.fillWidth: true
            SplitView.minimumWidth: 400

            ScrollList {
                id: _view

                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.rightMargin: 5

                spacing: Metrics.gapM
                scrollbarAlwaysVisible: true

                model: scriptListModel
                delegate: ScriptUI {
                    Layout.margins: Metrics.gapL
                    width: _view.width
                }
            }

            Button {
                Layout.alignment: Qt.AlignHCenter | Qt.AlignBottom
                Layout.preferredHeight: 30
                Layout.bottomMargin: 10

                text: "Add Script"

                onClicked: () => _selectScript.open()
            }
        }

        ScriptConfiguration {
            id: _config

            SplitView.fillHeight: true
            SplitView.minimumWidth: 500
        }
    }

    component ScriptUI : RowLayout {
        id: _item

        required property string path
        required property string name
        required property var variables

        AppIcon {
            Layout.leftMargin: 10
            name: "duplicate"
        }

        Label {
            id: _path

            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: _view.width - 400

            text: _item.path
            leftPadding: Metrics.gapL
            elide: Text.ElideMiddle

            ToolTip {
                text: _path.text
                // Set an upper width of the tooltip to force word wrap on
                // long texts.
                width: contentWidth > 500 ? 500 : contentWidth + 20
                visible: _hoverPath.hovered
                delay: 500
            }

            HoverHandler {
                id: _hoverPath
                acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            }
        }

        Spacer {}

        Label {
            id: _name

            Layout.preferredWidth: 200
            Layout.alignment: Qt.AlignVCenter

            text: _item.name
            rightPadding: Metrics.labelTrailingReserve
            elide: Text.ElideMiddle

            ToolTip {
                text: _name.text
                // Set an upper width of the tooltip to force word wrap on
                // long texts.
                width: contentWidth > 500 ? 500 : contentWidth + 20
                visible: _hoverName.hovered
                delay: 500
            }

            HoverHandler {
                id: _hoverName
                acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            }
        }

        ToolButton {
            icon.name: "edit"

            onClicked: {
                _renameScriptDialog.text = name
                _renameScriptDialog.callback = (value) => {
                    scriptListModel.renameScript(path, name, value)
                }
                _renameScriptDialog.visible = true
            }
        }

        ToolButton {
            icon.name: "options"

            onClicked: {
                _config.model = variables
            }
        }

        ToolButton {
            Layout.rightMargin: 20
            icon.name: "delete"

            onClicked: () => scriptListModel.removeScript(path, name)
        }
    }
}
