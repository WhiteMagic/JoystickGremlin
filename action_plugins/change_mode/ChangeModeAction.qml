// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2024 Lionel Ott
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
import QtQuick.Layouts
import QtQuick.Window

import QtQuick.Controls.Universal

import Gremlin.Profile
import Gremlin.ActionPlugins
import "../../qml"


Item {
    id: _root

    property ChangeModeModel action
    property ModeHierarchyModel modes : backend.modeHierarchy

    implicitHeight: _content.height

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right


        ComboBox {
            id: _changeType

            Layout.alignment: Qt.AlignTop

            model: ["Switch", "Previous", "Unwind", "Cycle", "Temporary"]

            Component.onCompleted: function() {
                currentIndex = find(_root.action.changeType)
            }

            onActivated: function() {
                _root.action.changeType = currentValue
            }
        }

        // Mode switch selection UI
        RowLayout {
            visible: _changeType.currentValue === "Switch"

            Label {
                text: "Switch to mode"
            }

            ComboBox {
                id: _switch_combo

                model: _root.modes.modeList
                textRole: "name"
                valueRole: "name"

                Component.onCompleted: function() {
                    currentIndex = find(_root.action.targetModes[0])
                }

                onActivated: function() {
                    _root.action.setTargetMode(currentValue, 0)
                }

                Connections {
                    target: _changeType
                    function onActivated() {
                        if(visible)
                        {
                            _switch_combo.currentIndex = _switch_combo.find(
                                _root.action.targetModes[0]
                            )
                        }
                    }
                }
            }
        }

        // Switch to previous mode UI
        RowLayout {
            visible: _changeType.currentValue === "Previous"

            Label {
                text: "Change to the previously active mode"
            }
        }

        // Unwind one mode from the stack UI
        RowLayout {
            visible: _changeType.currentValue === "Unwind"

            Label {
                text: "Unwind one mode in the stack"
            }
        }

        // Mode cycle setup UI
        RowLayout {
            visible: _changeType.currentValue === "Cycle"

            Label {
                Layout.alignment: Qt.AlignTop

                text: "Cycle through these modes"
            }

            ColumnLayout {
                Layout.fillWidth: true

                Repeater {
                    model: _root.action.targetModes

                    RowLayout {
                        required property int index

                        ComboBox {
                            model: _root.modes.modeList
                            textRole: "name"
                            valueRole: "name"

                            Component.onCompleted: function() {
                                currentIndex = find(_root.action.targetModes[index])
                            }

                            onActivated: function() {
                                _root.action.setTargetMode(currentValue, index)
                            }
                        }

                        IconButton {
                            text: bsi.icons.remove

                            onClicked: {
                                _root.action.deleteTargetMode(index)
                            }
                        }
                    }
                }

                Button {
                    text: "Add mode"

                    onClicked: function() {
                        _root.action.addTargetMode()
                    }
                }

            }
        }

        // Temporary mode switch UI
        RowLayout {
            visible: _changeType.currentValue === "Temporary"

            Label {
                text: "Temporarily switch to mode"
            }

            ComboBox {
                id: temporary_combo

                model: _root.modes.modeList
                textRole: "name"
                valueRole: "name"

                Component.onCompleted: function() {
                    currentIndex = find(_root.action.targetModes[0])
                }

                onActivated: function() {
                    _root.action.setTargetMode(currentValue, 0)
                }

                Connections {
                    target: _changeType
                    function onActivated() {
                        if(visible)
                        {
                            temporary_combo.currentIndex = temporary_combo.find(
                                _root.action.targetModes[0]
                            )
                        }
                    }
                }
            }
        }

        LayoutSpacer {}
    }
}