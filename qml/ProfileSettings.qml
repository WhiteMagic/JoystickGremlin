// -*- coding: utf-8; -*-
//
// Copyright (C) 2025 Lionel Ott
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
import QtQuick.Dialogs
import QtQuick.Layouts
import Qt.labs.qmlmodels

import Gremlin.Profile

import "helpers.js" as Helpers


Item {
    id: _root

    readonly property int userEntryColumnWidth: 250
    readonly property int userEntryColumnPadding: 50

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 10

        ColumnLayout {
            UIHeader {
                text: "Startup Mode"
            }

            RowLayout {
                ComboBox {
                    Layout.preferredWidth: userEntryColumnWidth
                    Layout.rightMargin: userEntryColumnPadding

                    model: StartupModeModel {}

                    textRole: "label"
                    valueRole: "value"
                    currentIndex: model.currentSelectionIndex

                    onActivated: () => {
                        model.currentSelectionIndex = currentIndex
                    }
                }

                UIText {
                    text: "Selection defines what mode Gremlin should start " +
                        "in when the profile is activated. \"Use Heuristic\" " +
                        "lets Gremlin decide, otherwise the selected mode is " +
                        "used."
                }
            }

        }

        ColumnLayout {
            UIHeader {
                text: "vJoy Behavior"
            }

            RowLayout {
                ListView {
                    Layout.preferredWidth: userEntryColumnWidth
                    Layout.rightMargin: userEntryColumnPadding
                    implicitHeight: contentHeight

                    model: VJoyInputOrOutputModel {}

                    delegate: Switch {
                        required property int vid
                        required property bool isOutput

                        text: `vJoy ${vid} as output ${isOutput}`

                        checked: isOutput
                        onToggled: () => { isOutput = checked }
                    }
                }

                UIText {
                    text: "Determines if a vJoy devices are treated as an" +
                        "input or output device by Gremlin. If treated " +
                        "as an output device it can be used with the " +
                        "'Map to vJoy' action. If treated as an input device" +
                        "the vJoy device is treated as if it was any other " +
                        "joystick. This is useful when multiple vJoy " +
                        "devices exist and are used by different programs."
                }
            }
        }

        ColumnLayout {
            UIHeader {
                text: "vJoy Initial Values"
            }

            RowLayout {
                TreeView {
                    Layout.preferredWidth: userEntryColumnWidth
                    Layout.rightMargin: userEntryColumnPadding
                    implicitHeight: contentHeight

                    model: VJoyInitialValuesModel {}

                    // delegate: TreeViewDelegate {
                    //     Label {
                    //         text: "Just some test"
                    //     }
                    // }
                    delegate: TreeViewDelegate {
                        contentItem: Label {
                            text: "model.display"
                        }
                    }
                }
                

                UIText {
                    text: "Defines the initial values for vJoy axes to use " +
                        "when a profile is activated."
                }
            }
        }

        ColumnLayout {
            Layout.fillHeight: true
        }
    }

    // Header text component
    component UIHeader : Text {
        font.pointSize: 14
        font.weight: 500
        font.family: "Segoe UI"
    }

    // Standard text component
    component UIText : Text {
        Layout.fillWidth: true
        horizontalAlignment: Text.AlignJustify
        wrapMode: Text.Wrap

        font.pointSize: 11
        font.family: "Segoe UI"
    }
}