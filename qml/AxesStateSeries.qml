// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2022 Lionel Ott
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
import QtCharts

import QtQuick.Controls.Universal

import Gremlin.Device


Item {
    id: _root

    property string deviceGuid
    property string title
    property var colors: [
        "#1f77b4",
        "#d62728",
        "#2ca02c",
        "#ff7f0e",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
        "#9467bd",
    ]

    function compute_height(available_width)
    {
        return _chart.height + _header.height
    }

    DeviceAxisSeries {
        id: _axis_series

        guid: deviceGuid

        onDeviceChanged: function() {
            _chart.removeAllSeries()

            for(var i=0; i<axisCount; i++)
            {
                var series = _chart.createSeries(
                    ChartView.SeriesTypeLine,
                    "Axis " + axisIdentifier(i),
                    _x_axis,
                    _y_axis
                )
               series.color = colors[i]
            }
        }
    }

    Timer {
        interval: 10
        running: true
        repeat: true
        onTriggered: function()
        {
            for(var i=0; i<_chart.count; i++)
            {
                _axis_series.updateSeries(_chart.series(i), i)
            }
        }
    }

    ColumnLayout {
        anchors.left: parent.left
        anchors.right: parent.right

        RowLayout {
            id: _header

            DisplayText {
                text: title + " - Axes"
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter

                height: 2
                color: Universal.baseLowColor
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 300

            z: -1
            clip: true

            ChartView {
                id: _chart

                margins {
                    top: 0
                    bottom: 0
                    left: 0
                    right: 0
                }

                y: -20
                width: parent.width
                height: parent.height

                antialiasing: true

                ValueAxis {
                    id: _y_axis

                    min: -1
                    max: 1
                }

                ValueAxis {
                    id: _x_axis

                    min: -_axis_series.windowSize
                    max: 0
                }
            }
        }
    }

}