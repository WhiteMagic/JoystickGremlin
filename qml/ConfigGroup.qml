// -*- coding: utf-8; -*-
//
// Copyright (C) 2022 Lionel Ott
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
import Qt.labs.qmlmodels

import Gremlin.Config
import "helpers.js" as Helpers


ColumnLayout {
    required property int index
    required property string groupName
    required property ConfigEntryModel entryModel

    anchors.left: parent.left
    anchors.right: parent.right

    // Group header
    RowLayout {
        Layout.fillWidth: true
        Layout.preferredHeight: 50

        UIHeader {
            text: Helpers.capitalize(groupName)
        }
    }

    // Display config entries
    Repeater {
        model: entryModel
        delegate: _entryDelegateChooser
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

    // Delegate rendering individual configuration option styles
    DelegateChooser {
        id: _entryDelegateChooser
        role: "data_type"

        // On/off options
        DelegateChoice {
            roleValue: "bool"

            RowLayout {
                Layout.fillWidth: true

                Switch {
                    Layout.alignment: Qt.AlignTop
                    checked: value

                    text: checked ? "On" : "Off"

                    onToggled: () => value = checked
                }

                UIText {
                    text: description
                }
            }
        }
        // Floating point value inputs
        DelegateChoice {
            roleValue: "float"

            ColumnLayout {
                Layout.fillWidth: true

                UIText {
                    text: description
                }

                FloatSpinBox {
                    value: value
                    minValue: properties.min
                    maxValue: properties.max

                    onValueModified: (newValue) => { value = newValue }
                }
            }
        }
        // Integer value inputs
        DelegateChoice {
            roleValue: "int"

            ColumnLayout {
                Layout.fillWidth: true

                UIText {
                    text: description
                }

                SpinBox {
                    value: model.value
                    from: properties.min
                    to: properties.max

                    onValueModified: () => model.value = value
                }
            }
        }
        // Textual inputs
        DelegateChoice {
            roleValue: "string"

            ColumnLayout {
                Layout.fillWidth: true

                UIText {
                    text: description
                }

                TextField {
                    text: value

                    Layout.fillWidth: true

                    onTextEdited: () => value = text
                }
            }
        }
        // Drop down menu selection
        DelegateChoice {
            roleValue: "selection"

            ColumnLayout {
                Layout.fillWidth: true

                UIText {
                    text: description
                }

                ComboBox {
                    model: properties.valid_options

                    implicitContentWidthPolicy: ComboBox.WidestText

                    Component.onCompleted: () => currentIndex = find(value)
                    onActivated: () => value = currentValue
                }
            }
        }
        // Meta Option dynamic loading
        DelegateChoice {
            roleValue: "meta_option"

            ColumnLayout {
                Layout.fillWidth: true

                UIText {
                    text: description
                }

                // Dynamic item container
                DynamicItemLoader {
                    id: metaLoader
                    // Layout.fillWidth: true

                    // 'value' is assumed to be the qrc:/... URL for the meta option QML
                    qmlPath: value

                    // Provide additional properties to the loaded component if needed
                    // (delete if not required)
                    injectedProperties: {
                        // Example placeholders:
                        // initialValue: model.value,
                        // description: description
                    }

                    // Optional: force a reload even when file path string stays the same
                    // forceReloadOnIdenticalPath: true

                    // Optional: react to successful load
                    onLoaded: (item) => {
                        // If the loaded item exposes a property you want to initialize,
                        // you can set it here. Keep empty if not needed.
                    }

                    // Optional: log errors
                    onLoadError: (src, err) => console.warn("Meta option load error:", src, err)
                }

            }
        }

    }
}