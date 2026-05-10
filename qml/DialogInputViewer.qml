// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.Device
import Gremlin.Style

Window {
    id: _inputViewer

    width: 1400
    height: 800
    minimumWidth: 900
    minimumHeight: 500

    color: Style.background
    Universal.theme: Style.theme

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
    }

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
            Layout.rightMargin: 10
            Layout.minimumWidth: 250
            Layout.maximumWidth: 400
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
                IconButton {
                    id: _foldButton

                    checkable: true
                    checked: false
                    text: checked ? bsi.icons.folded : bsi.icons.unfolded
                }

                JGText {
                    Layout.fillWidth: true

                    text: name
                }
            }

            // Per device visualization toggles.
            ColumnLayout {
                visible: _foldButton.checked

                Layout.leftMargin: _foldButton.width

                Switch {
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
                Switch {
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
                Switch {
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
