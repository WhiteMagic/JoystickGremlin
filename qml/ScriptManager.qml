// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import Qt.labs.qmlmodels

import Gremlin.Script

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
            scriptListModel.addScript(Helpers.pythonizePath(selectedFile))
        }
    }

    // Dialog to rename a script
    TextInputDialog {
        id: _renameScriptDialog

        visible: false
        width: 300

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

            JGListView {
                id: _view

                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.rightMargin: 5

                spacing: 10
                scrollbarAlwaysVisible: true

                model: scriptListModel
                delegate: ScriptUI {
                    Layout.margins: 10
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

        JGText {
            Layout.leftMargin: 10
            text: bsi.icons.script
            font.pixelSize: 18
        }

        JGText {
            id: _path

            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: _view.width - 400

            text: _item.path
            leftPadding: 10
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

        LayoutHorizontalSpacer {}

        JGText {
            id: _name

            Layout.preferredWidth: 200
            Layout.alignment: Qt.AlignVCenter

            text: _item.name
            rightPadding: 50
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

        IconButton {
            text: bsi.icons.edit

            onClicked: {
                _renameScriptDialog.text = name
                _renameScriptDialog.callback = (value) => {
                    scriptListModel.renameScript(path, name, value)
                }
                _renameScriptDialog.visible = true
            }
        }

        IconButton {
            text: bsi.icons.configure

            onClicked: {
                _config.model = variables
            }
        }

        IconButton {
            Layout.rightMargin: 20
            text: bsi.icons.trash

            onClicked: () => scriptListModel.removeScript(path, name)
        }
    }
}
