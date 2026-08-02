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

    // Local to this file -- the two SplitView panes' width floors, not a shared design concept.
    readonly property int scriptListMinWidth: Metrics.dp(400)
    readonly property int configMinWidth:     Metrics.dp(500)
    readonly property int pathWidthReserve:   Metrics.dp(400)
    readonly property int nameLabelWidth:     Metrics.dp(200)

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
        width: Metrics.dp(300)

        property var callback: null

        onAccepted: function(value)
        {
            callback(value)
            visible = false
        }
    }

    SplitView {
        anchors.fill: parent
        anchors.leftMargin: Metrics.gapM

        ColumnLayout {
            SplitView.fillHeight: true
            SplitView.fillWidth: true
            SplitView.minimumWidth: _root.scriptListMinWidth

            ScrollList {
                id: _view

                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.rightMargin: Metrics.gapS

                spacing: Metrics.gapM
                scrollbarAlwaysVisible: true

                model: scriptListModel
                delegate: ScriptUI {
                    Layout.margins: Metrics.gapL
                    width: _view.width
                }
            }

            Button {
                Layout.alignment: Qt.AlignHCenter
                Layout.bottomMargin: Metrics.gapM

                text: "Add Script"

                onClicked: () => _selectScript.open()
            }
        }

        ScriptConfiguration {
            id: _config

            SplitView.fillHeight: true
            SplitView.minimumWidth: _root.configMinWidth
        }
    }

    component ScriptUI : RowLayout {
        id: _item

        required property string path
        required property string name
        required property var variables

        AppIcon {
            Layout.leftMargin: Metrics.gapM
            name: "duplicate"
        }

        Label {
            id: _path

            Layout.alignment: Qt.AlignVCenter
            Layout.preferredWidth: _view.width - _root.pathWidthReserve

            text: _item.path
            leftPadding: Metrics.gapL
            elide: Text.ElideMiddle

            ToolTip {
                text: _path.text
                // Set an upper width of the tooltip to force word wrap on
                // long texts.
                width: Metrics.tooltipWidth(contentWidth)
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

            Layout.preferredWidth: _root.nameLabelWidth
            Layout.alignment: Qt.AlignVCenter

            text: _item.name
            rightPadding: Metrics.gapL
            elide: Text.ElideMiddle

            ToolTip {
                text: _name.text
                // Set an upper width of the tooltip to force word wrap on
                // long texts.
                width: Metrics.tooltipWidth(contentWidth)
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
            Layout.rightMargin: Metrics.gapL
            icon.name: "delete"

            onClicked: () => scriptListModel.removeScript(path, name)
        }
    }
}
