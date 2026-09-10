// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Kobold.Controls
import Kobold.Foundation

Window {
    id: _calibrationDialog

    minimumWidth: Metrics.dp(850)
    maximumWidth: Metrics.dp(850)
    minimumHeight: Metrics.dp(600)

    // Local to this file -- CalibrationItem delegate layout, not a shared design concept.
    readonly property int rawLabelWidth:     Metrics.dp(75)
    readonly property int valueFieldWidth:   Metrics.dp(100)
    readonly property int progressBarHeight: Metrics.dp(30)
    readonly property int buttonColumnWidth: Metrics.dp(150)

    color: Theme.bg

    title: "Calibration"


    Connections {
        target: _calibrationDialog

        function onClosing() {
            _axisView.model.destroy()
            _axisView.destroy()
            _deviceData.destroy()
            backend.resumeInputHighlighting()
        }
    }

    Component.onCompleted: () => {
        backend.pauseInputHighlighting()
    }

    DeviceListModel {
        id: _deviceData

        deviceType: "physical"
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.leftMargin: Metrics.gapM

        RowLayout {
            Layout.bottomMargin: Metrics.gapL
            Layout.topMargin: Metrics.gapL

            Label {
                Layout.preferredWidth: Metrics.dp(150)
                text: "Device to calibrate"
            }

            ComboBox {
                id: _deviceSelection

                model: _deviceData
                textRole: "name"
                valueRole: "guid"
                implicitContentWidthPolicy: ComboBox.WidestText
            }
        }

        ScrollList {
            id: _axisView

            scrollbarAlwaysVisible: true
            spacing: Metrics.gapM
            Layout.fillWidth: true
            Layout.fillHeight: true

            model: AxisCalibration {
                guid: _deviceSelection.currentValue
            }

            delegate: CalibrationItem {
                width: ListView.view.width
            }
        }
    }


    component CalibrationItem : ColumnLayout {

        // Specify all properties we need from the model
        required property int index
        required property string identifier
        required property int calibratedValue
        required property int rawValue
        required property int low
        required property int centerLow
        required property int centerHigh
        required property int high
        required property bool withCenter
        required property bool unsavedChanges
        required property var model

        // Display axis name and current raw value and axis type
        RowLayout {
            Layout.rightMargin: Metrics.gapL

            Label {
                Layout.fillWidth: true

                text: identifier
                wrapMode: Text.Wrap
            }

            Label {
                Layout.preferredWidth: _calibrationDialog.rawLabelWidth
                Layout.rightMargin: Metrics.gapS

                text: "Raw"
                horizontalAlignment: Text.AlignRight
            }

            TextField {
                Layout.preferredWidth: _calibrationDialog.valueFieldWidth

                text: rawValue
            }

            Label {
                Layout.preferredWidth: _calibrationDialog.valueFieldWidth

                text: "With center"
                horizontalAlignment: Text.AlignRight
            }
            CheckBox {
                Layout.preferredWidth: _calibrationDialog.valueFieldWidth

                text: checked ? "Yes" : "No"
                checked: model.withCenter
                onToggled: {
                    model.withCenter = checked
                }
            }
        }


        RowLayout {

            Layout.rightMargin: Metrics.gapL

            // Show live axis sliders and calibration values
            ColumnLayout {
                Layout.fillWidth: true

                BetterProgressBar {
                    id: _progressRaw

                    Layout.preferredHeight: _calibrationDialog.progressBarHeight
                    Layout.fillWidth: true

                    value: rawValue
                    from: -32768
                    to: 32767
                }
                BetterProgressBar {
                    id: _progressCalibrated

                    Layout.preferredHeight: _calibrationDialog.progressBarHeight
                    Layout.fillWidth: true

                    value: calibratedValue
                    from: -32768
                    to: 32767
                }

                Rectangle {
                    Layout.fillHeight: true
                }

                // Show calibration values
                RowLayout {
                    CalibrationSpinBox {
                        id: _sbLow

                        value: low
                        from: -32768
                        to: _sbCLow.value

                        onValueModified: model.low = Qt.binding(() => value)
                    }
                    Spacer {
                    }
                    CalibrationSpinBox {
                        id: _sbCLow

                        visible: model.withCenter
                        value: centerLow
                        from: _sbLow.value
                        to: _sbCHigh.value

                        onValueModified: model.centerLow = Qt.binding(() => value)
                    }
                    CalibrationSpinBox {
                        id: _sbCHigh

                        visible: model.withCenter
                        value: centerHigh
                        from: _sbCLow.value
                        to: _sbHigh.value

                        onValueModified: model.centerHigh = Qt.binding(() => value)
                    }
                    Spacer {
                    }
                    CalibrationSpinBox {
                        id: _sbHigh

                        value: high
                        from: _sbCHigh.value
                        to: 32767

                        onValueModified: model.high = Qt.binding(() => value)
                    }
                }
            }

            // Buttons to control calibration
            ColumnLayout {
                Layout.preferredWidth: _calibrationDialog.buttonColumnWidth
                Layout.alignment: Qt.AlignBottom

                RowLayout {
                    ToolButton {
                        Layout.fillWidth: true

                        icon.name: "reset"

                        onClicked: () => _axisView.model.reset(index)
                    }
                    ToolButton {
                        Layout.fillWidth: true

                        icon.name: "save_profile"

                        onClicked: () => _axisView.model.save(index)

                        Rectangle {
                            visible: unsavedChanges
                            anchors.fill: parent
                            anchors.margins: -2
                            radius: Metrics.radius
                            color: "transparent"
                            border.width: 2
                            border.color: Theme.warning
                        }
                    }
                }

                Button {
                    id: _btnCenterCalibration

                    Layout.preferredWidth: _calibrationDialog.buttonColumnWidth
                    text: "Calibrate center"
                    visible: model.withCenter

                    checkable: true
                    onToggled: () => {
                        _axisView.model.calibrateCenter(index, checked)
                        _btnExtremaCalibration.checked = false
                    }
                }
                Spacer {
                    visible: !model.withCenter
                }
                Button {
                    id: _btnExtremaCalibration

                    Layout.preferredWidth: _calibrationDialog.buttonColumnWidth
                    text: "Calibrate extrema"

                    checkable: true
                    onToggled: {
                        _axisView.model.calibrateExtrema(index, checked)
                        _btnCenterCalibration.checked = false
                    }
                }
            }
        }

        // Spacer at the bottom to leave some empty space below the ListView
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: Metrics.gapM
        }
    }

    component CalibrationSpinBox : SpinBox {
        editable: true
        from: -32768
        to: 32767
        value: 0
    }
}
