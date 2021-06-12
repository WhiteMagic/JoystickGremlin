// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2020 Lionel Ott
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

import QtQuick 2.14
import QtQuick.Controls 2.14
import QtQuick.Controls.Universal 2.14
import QtQuick.Layouts 1.14

import gremlin.ui.profile 1.0
import gremlin.plugins 1.0
import "../../qml"


Item {
    id: _root

    property ActionNodeModel node
    property RemapModel action

    implicitHeight: _content.height

    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        VJoySelector {
            vjoyInputType: _root.action.vjoyInputType
            vjoyInputId: _root.action.vjoyInputId
            vjoyDeviceId: _root.action.vjoyDeviceId
            validTypes: [inputBinding.behavior]

            onVjoyInputIdChanged: { _root.action.vjoyInputId = vjoyInputId }
            onVjoyDeviceIdChanged: { _root.action.vjoyDeviceId = vjoyDeviceId }
            onVjoyInputTypeChanged: { _root.action.vjoyInputType = vjoyInputType }
        }

        // UI for a physical axis behaving as an axis
        Loader {
            active: _root.action.vjoyInputType == "axis"
            Layout.fillWidth: true

            sourceComponent: Row {
                RadioButton {
                    text: "Absolute"
                    checked: true

                    onCheckedChanged: {
                        _root.action.axisMode = "absolute"
                    }
                }
                RadioButton {
                    id: _relativeMode
                    text: "Relative"

                    onCheckedChanged: {
                        _root.action.axisMode = "relative"
                    }
                }

                Label {
                    text: "Scaling"
                    anchors.verticalCenter: parent.verticalCenter
                    visible: _relativeMode.checked
                }

                FloatSpinBox {
                    visible: _relativeMode.checked
                    minValue: 0
                    maxValue: 100
                    value: 1
                    stepSize: 0.1

                    onValueChanged: {
                        _root.action.axisScaling = value
                    }
                }
            }
        }
    }
}