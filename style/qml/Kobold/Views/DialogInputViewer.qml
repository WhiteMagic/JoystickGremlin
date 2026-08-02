// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Kobold.Foundation

import "helpers.js" as Helpers

Window {
    id: _inputViewer

    minimumWidth: Metrics.dp(900)
    minimumHeight: Metrics.dp(500)

    // Local to this file -- the device-list sidebar's width range, not a shared design concept.
    readonly property int deviceListMinWidth: Metrics.dp(250)
    readonly property int deviceListMaxWidth: Metrics.dp(400)

    property var _geom: backend.windowGeometry(
        "input-viewer-geometry", Metrics.windowWidth, Metrics.dp(800),
        minimumWidth, minimumHeight
    )
    // True until Component.onCompleted -- suppresses the save that would
    // otherwise fire from the initial x/y/width/height binding evaluation.
    property bool _restoringGeometry: true

    x: _geom.x
    y: _geom.y
    width: _geom.width
    height: _geom.height

    color: Theme.bg

    title: "Input Viewer"

    Connections {
        target: _inputViewer

        function onClosing() {
            _stateDisplay.children.forEach((child) => {
                child.destroy()
            })
            _deviceData.destroy()
            backend.resumeInputHighlighting()
        }
    }

    Component.onCompleted: () => {
        backend.pauseInputHighlighting()
        _restoringGeometry = false
    }

    Timer {
        id: _geometrySaveTimer
        interval: 500
        repeat: false
        onTriggered: _geom.save(_inputViewer.x, _inputViewer.y, _inputViewer.width, _inputViewer.height)
    }

    onXChanged: if (!_restoringGeometry) _geometrySaveTimer.restart()
    onYChanged: if (!_restoringGeometry) _geometrySaveTimer.restart()
    onWidthChanged: if (!_restoringGeometry) _geometrySaveTimer.restart()
    onHeightChanged: if (!_restoringGeometry) _geometrySaveTimer.restart()

    DeviceListModel {
        id: _deviceData

        deviceType: "all"
    }

    function create_widget(qml_path, guid, name) {
        let component = Qt.createComponent(Qt.resolvedUrl(qml_path))
        if (component.status == Component.Ready) {
            var widget = component.createObject(
                _stateDisplay,
                {
                    deviceGuid: guid,
                    title: name,
                    "Layout.fillWidth": true
                }
            );
        }

        return widget
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
                    model: _deviceData
                    delegate: _deviceDelegate
                }
            }
        }

        // Dynamic scrollview that contains dynamically generated widgets.
        ScrollView  {
            id: _dynamicScroll

            Layout.fillWidth: true
            Layout.fillHeight: true

            Component.onCompleted: () => {
                _dynamicScroll.contentItem.boundsMovement = Flickable.StopAtBounds
                _dynamicScroll.contentItem.boundsBehavior = Flickable.StopAtBounds
            }

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

            // Variable holding references to the widgets visualizing device
            // input states.
            property var widget_btn_hat
            property var widget_axis_temp
            property var widget_axis_cur

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
                            widget_axis_temp = create_widget(
                                "AxesStateSeries.qml",
                                guid,
                                name
                            )
                        } else {
                            widget_axis_temp.destroy()
                        }
                    }
                }
                CheckBox {
                    text: "Axes - Current"

                    onClicked: () => {
                        if(checked) {
                            widget_axis_cur = create_widget(
                                "AxesStateCurrent.qml",
                                guid,
                                name
                            )
                        } else {
                            widget_axis_cur.destroy()
                        }
                    }
                }
                CheckBox {
                    text: "Buttons & Hats"

                    onClicked: () => {
                        if(checked) {
                            widget_btn_hat = create_widget(
                                "ButtonState.qml",
                                guid,
                                name
                            )
                        } else {
                            widget_btn_hat.destroy()
                        }
                    }
                }
            }
        }
    }
}
