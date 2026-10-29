// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Gremlin.UI
import Kobold.Foundation
import "helpers.js" as Helpers

Window {
    id: _inputViewer

    minimumWidth: Metrics.dp(900)
    minimumHeight: Metrics.dp(500)

    readonly property int deviceListMinWidth: Metrics.dp(250)
    readonly property int deviceListMaxWidth: Metrics.dp(400)
    readonly property DeviceListModel _deviceData:
        ModelFactory.deviceListModel(_inputViewer, "all")

    property var _geom: null
    // True until Component.onCompleted, suppresses saving geometry information before
    // restoring saved values.
    property bool _restoringGeometry: true

    color: Theme.bg

    title: "Input Viewer"

    Connections {
        target: _inputViewer

        function onClosing() {
            _stateDisplay.children.forEach((child) => {
                child.destroy()
            })
            backend.resumeInputHighlighting()
        }
    }

    Component.onCompleted: () => {
        backend.pauseInputHighlighting()
        _geom = ModelFactory.windowGeometry(
            _inputViewer, "input-viewer-geometry", Metrics.windowWidth, Metrics.dp(800),
            minimumWidth, minimumHeight
        )
        x = _geom.x
        y = _geom.y
        width = _geom.width
        height = _geom.height
        _restoringGeometry = false
    }

    // Saves window geometry after a short delay, to avoid saving geometry while it is
    // still actively being changed.
    Timer {
        id: _geometrySaveTimer
        interval: 500
        repeat: false
        onTriggered: {
            _geom.save(
                _inputViewer.x,
                _inputViewer.y,
                _inputViewer.width,
                _inputViewer.height
            )
        }
    }

    onXChanged: if (!_restoringGeometry) _geometrySaveTimer.restart()
    onYChanged: if (!_restoringGeometry) _geometrySaveTimer.restart()
    onWidthChanged: if (!_restoringGeometry) _geometrySaveTimer.restart()
    onHeightChanged: if (!_restoringGeometry) _geometrySaveTimer.restart()

    function createWidget(typeName, guid, name) {
        let component = Qt.createComponent("Kobold.Views", typeName)
        if (component.status == Component.Error) {
            console.log(component.errorString())
            return null
        }

        return component.createObject(
            _stateDisplay,
            {
                deviceGuid: guid,
                title: name,
                "Layout.fillWidth": true
            }
        )
    }

    RowLayout {
        id: _root

        anchors.fill: parent

        ScrollView {
            Layout.alignment: Qt.AlignTop
            Layout.rightMargin: Metrics.gapM
            Layout.minimumWidth: _inputViewer.deviceListMinWidth
            Layout.maximumWidth: _inputViewer.deviceListMaxWidth
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent

                Repeater {
                    model: _inputViewer._deviceData
                    delegate: _deviceDelegate
                }
            }
        }

        // Dynamic scrollview that contains dynamically generated widgets.
        ScrollView  {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                id: _stateDisplay

                anchors.left: parent.left
                anchors.right: parent.right
            }
        }
    }

    // Display the collapsible visualization toggles for a single device.
    Component {
        id: _deviceDelegate

        ColumnLayout {
            id: _delegateContent

            required property int index
            required property string name
            required property string guid

            // Variable holding references to the widgets visualizing device input
            // states.
            property var widgetBtnHat
            property var widgetAxisTemp
            property var widgetAxisCur

            // Device header.
            RowLayout {
                ToolButton {
                    id: _foldButton

                    checkable: true
                    checked: false
                    icon.name: "chevron-down"
                    rotation: checked ? 0 : -90
                }

                Label {
                    Layout.fillWidth: true

                    text: name
                }
            }

            // Per device visualization toggles.
            ColumnLayout {
                visible: _foldButton.checked

                Layout.leftMargin: _foldButton.width

                CheckBox {
                    text: "Axes - Temporal"

                    onClicked: () => {
                        if(checked) {
                            widgetAxisTemp = createWidget(
                                "AxesStateSeries",
                                guid,
                                name
                            )
                            checked = !!widgetAxisTemp
                        } else if(widgetAxisTemp) {
                            widgetAxisTemp.destroy()
                            widgetAxisTemp = null
                        }
                    }
                }
                CheckBox {
                    text: "Axes - Current"

                    onClicked: () => {
                        if(checked) {
                            widgetAxisCur = createWidget(
                                "AxesStateCurrent",
                                guid,
                                name
                            )
                            checked = !!widgetAxisCur
                        } else if(widgetAxisCur) {
                            widgetAxisCur.destroy()
                            widgetAxisCur = null
                        }
                    }
                }
                CheckBox {
                    text: "Buttons & Hats"

                    onClicked: () => {
                        if(checked) {
                            widgetBtnHat = createWidget(
                                "ButtonState",
                                guid,
                                name
                            )
                            checked = !!widgetBtnHat
                        } else if(widgetBtnHat) {
                            widgetBtnHat.destroy()
                            widgetBtnHat = null
                        }
                    }
                }
            }
        }
    }
}
