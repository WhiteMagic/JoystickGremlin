// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Profile
import Gremlin.Style

Window {
    id: _root

    minimumWidth: 900
    minimumHeight: 500

    color: Style.background
    Universal.theme: Style.theme

    title: "Manage Modes"

    property ModeHierarchyModel modeHierarchy : ModeHierarchyModel {}
    property ModeListModel modeList : ModeListModel {}

    TextInputDialog {
        id: _textInput

        visible: false
        width: 500

        property var callback: null

        onAccepted: (value) => {
            callback(value)
            visible = false
        }
    }

    ColumnLayout {
        id: _content

        anchors.fill: parent
        anchors.topMargin: 10
        anchors.bottomMargin: 10

        JGListView  {
            Layout.fillWidth: true
            Layout.fillHeight: true

            scrollbarAlwaysVisible: true
            spacing: 10

            model: modeList
            delegate: _delegate
        }

        Button {
            Layout.alignment: Qt.AlignHCenter

            text: "Add Mode"

            onClicked: () => {
                let validNames = modeHierarchy.modeStringList()

                _textInput.title = "Add new mode"
                _textInput.text = "New mode"
                _textInput.validator = function(value)
                {
                    return !validNames.includes(value)
                }
                _textInput.callback = function(name) {
                    modeHierarchy.newMode(name)
                }
                _textInput.visible = true
            }
        }
    }

    Component {
        id: _delegate

        RowLayout {
            required property string name
            required property string parentName

            width: ListView.view.width
            height: _parentMode.height

            Label {
                Layout.fillWidth: true
                Layout.leftMargin: 10

                padding: 4

                text: name
            }

            ToolButton {
                icon.name: "edit"

                Layout.leftMargin: 10

                onClicked: () => {
                    let validNames = modeHierarchy.modeStringList()

                    _textInput.title = "Rename existing mode"
                    _textInput.text = name
                    _textInput.callback = function(value) {
                        modeHierarchy.renameMode(name, value)
                    }
                    _textInput.validator = function(value) {
                        return !validNames.includes(value)
                    }
                    _textInput.visible = true
                }
            }

            ComboBox {
                id: _parentMode

                Layout.preferredWidth: 200
                Layout.leftMargin: 10
                Layout.rightMargin: 10

                model: modeHierarchy.validParents(name)

                textRole: "value"
                valueRole: "value"

                onActivated: (index) => {
                    modeHierarchy.setParent(name, currentValue)
                }

                Component.onCompleted: () => {
                    currentIndex = indexOfValue(parentName)
                }
            }

            ToolButton {
                icon.name: "delete"

                Layout.rightMargin: 10

                onClicked: () => { modeHierarchy.deleteMode(name) }
            }
        }
    }
}
