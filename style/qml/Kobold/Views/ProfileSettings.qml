// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtQuick.Layouts
import Qt.labs.qmlmodels

import Gremlin.Profile
import Kobold.Controls
import Kobold.Foundation
import "helpers.js" as Helpers

Item {
    id: _root

    readonly property int userEntryColumnWidth: 350
    readonly property int userEntryColumnPadding: 50

    property ProfileSettingsModel settingsModel


    ScrollView {
        anchors.fill: parent

        // Ensure the content doesn't cause horizontal scrolling.
        contentWidth: availableWidth
        padding: Metrics.gapL

        // Disable annoying mobile device scrolling behaviors.
        ScrollBar.vertical.interactive: true
        Component.onCompleted: {
            contentItem.boundsMovement = Flickable.StopAtBounds
        }

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: Metrics.gapL

            ColumnLayout {
                Layout.fillWidth: true

                UIHeader {
                    text: "Startup Mode"
                }

                RowLayout {
                    ComboBox {
                        Layout.alignment: Qt.AlignTop
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
                        Layout.fillWidth: true

                        text: "Selection defines what mode Gremlin should start " +
                            "in when the profile is activated. \"Use Heuristic\" " +
                            "lets Gremlin decide, otherwise the selected mode is " +
                            "used."
                    }
                }

            }

            ColumnLayout {
                Layout.fillWidth: true

                UIHeader {
                    text: "Macro Default Delay"
                }

                RowLayout {
                    DoubleSpinBox {
                        Layout.alignment: Qt.AlignTop
                        Layout.preferredWidth: userEntryColumnWidth
                        Layout.rightMargin: userEntryColumnPadding

                        from: 0.0
                        to: 10.0
                        stepSize: 0.1
                        decimals: 3

                        value: settingsModel.macroDefaultDelay
                        onValueModified: (newValue) => {
                            settingsModel.macroDefaultDelay = newValue
                        }
                    }


                    UIText {
                        Layout.fillWidth: true

                        text: "Delay inserted between macro actions in " +
                            "seconds if no pause action is present."
                    }
                }
            }

            ColumnLayout {
                Layout.fillWidth: true

                UIHeader {
                    text: "vJoy Behavior"
                }

                RowLayout {
                    ListView {
                        Layout.alignment: Qt.AlignTop
                        Layout.preferredWidth: userEntryColumnWidth
                        Layout.rightMargin: userEntryColumnPadding
                        implicitHeight: contentHeight

                        model: VJoyInputOrOutputModel {}

                        delegate: RowLayout {
                            Label {
                                text: `vJoy ${vid} is`
                                Layout.preferredWidth: 75
                            }
                            Switch {
                                text: checked ? "Input" : "Output"

                                checked: isInput
                                onToggled: () => { isInput = checked }
                            }
                        }
                    }

                    UIText {
                        Layout.fillWidth: true

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
                Layout.fillWidth: true

                UIHeader {
                    text: "vJoy Initial Values"
                }

                RowLayout {
                    ScrollList {
                        Layout.preferredWidth: userEntryColumnWidth
                        Layout.rightMargin: userEntryColumnPadding
                        implicitHeight: contentHeight

                        spacing: Metrics.gapL

                        model: OutputVJoyListModel {}

                        delegate: ColumnLayout {
                            Layout.fillWidth: true

                            Label {
                                text: `vJoy ${vjoyId}`
                            }

                            Divider {
                                Layout.fillWidth: true
                            }

                            OutputVJoyInitialValueEntryDelegate {
                                dataModel: initialValuesModel
                            }
                        }
                    }

                    UIText {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignTop

                        text: "Defines the initial values for vJoy axes to use " +
                            "when a profile is activated."
                    }
                }
            }

            ColumnLayout {
                Layout.fillHeight: true
            }
        }
    }

    // Header text component
    component UIHeader : Label {
        font.weight: FontType.semiBold
    }

    // Standard text component
    component UIText : Label {
        Layout.fillWidth: true
        horizontalAlignment: Text.AlignJustify
        wrapMode: Text.Wrap

        font.pixelSize: Metrics.textDetail
        color: Theme.fgMuted
    }

    component OutputVJoyInitialValueEntryDelegate : ColumnLayout {
        property alias dataModel : _repeater.model

        Repeater {
            id: _repeater

            delegate: RowLayout {
                Label {
                    text: label
                    Layout.preferredWidth: 100
                }

                DoubleSpinBox {
                    from: -1.0
                    to: 1.0
                    stepSize: 0.05

                    // internalWidth: 130

                    value: model.value
                    onValueModified: (newValue) => { model.value = newValue }
                }
            }
        }
    }
}
