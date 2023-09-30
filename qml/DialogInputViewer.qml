// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2023 Lionel Ott
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

import Gremlin.Device


Window {
    minimumWidth: 900
    minimumHeight: 500

    title: "Input Viewer"

    DeviceListModel {
        id: _deviceData

        deviceType: "all"
    }

    function recompute_height()
    {
        for(let i=0; i<_stateDisplay.children.length; ++i)
        {
            var elem = _stateDisplay.children[i]
            elem.implicitHeight = elem.compute_height(_stateDisplay.width)
        }
    }

    function create_widget(qml_path, guid, name)
    {
        var component = Qt.createComponent(Qt.resolvedUrl(qml_path))
        var widget = component.createObject(
            _stateDisplay,
            {
                deviceGuid: guid,
                title: name
            }
        )

        widget.Layout.fillWidth = true
        recompute_height()
        return widget
    }

    RowLayout {
        id: _root

        anchors.fill: parent

        ScrollView {
            Layout.alignment: Qt.AlignTop
            Layout.minimumWidth: 250
            Layout.fillWidth: false
            Layout.fillHeight: true

            ColumnLayout {
                anchors.fill: parent

                Repeater {
                    model: _deviceData
                    delegate: _deviceDelegate
                }
            }
        }

        // Some dynamic scrollable thing that has UI widgets generated dynamically
        ScrollView  {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ColumnLayout {
                id: _stateDisplay

                anchors.left: parent.left
                anchors.right: parent.right

                onWidthChanged: function() {
                    recompute_height()
                }
            }
        }
    }

    // Display the collapsible visualization toggles for a single device
    Component {
        id: _deviceDelegate

        ColumnLayout {
            id: _delegateContent

            required property int index
            required property string name
            required property string guid

            // Variable holding references to the widgets visualizing device
            // input states
            property var widget_btn_hat
            property var widget_axis_temp
            property var widget_axis_cur

            // Device header
            RowLayout {
                IconButton {
                    id: _foldButton

                    checkable: true
                    checked: false
                    text: checked ? Constants.folded : Constants.unfolded
                }

                DisplayText {
                    text: name
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignVCenter

                    height: 2
                    color: Universal.baseLowColor
                }
            }

            // Per device visualization toggles
            ColumnLayout {
                visible: _foldButton.checked

                Layout.leftMargin: _foldButton.width

                Switch {
                    text: "Axes - Temporal"

                    onClicked: function()
                    {
                        if(checked)
                        {
                            widget_axis_temp = create_widget(
                                "AxesStateSeries.qml",
                                guid,
                                name
                            )
                        }
                        else
                        {
                            widget_axis_temp.destroy()
                        }
                    }
                }
                Switch {
                    text: "Axes - Current"

                    onClicked: function()
                    {
                        if(checked)
                        {
                            widget_axis_cur = create_widget(
                                "AxesStateCurrent.qml",
                                guid,
                                name
                            )
                        }
                        else
                        {
                            widget_axis_cur.destroy()
                        }
                    }
                }
                Switch {
                    text: "Buttons & Hats"

                    onClicked: function()
                    {
                        if(checked)
                        {
                            widget_btn_hat = create_widget(
                                "ButtonState.qml",
                                guid,
                                name
                            )
                        }
                        else
                        {
                            widget_btn_hat.destroy()
                        }
                    }
                }
            }
        }
    }
}