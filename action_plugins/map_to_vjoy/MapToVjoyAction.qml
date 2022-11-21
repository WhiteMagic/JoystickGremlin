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
import QtQuick.Controls.Universal
import QtQuick.Layouts

import Gremlin.Profile
import Gremlin.ActionPlugins
import "../../qml"


Item {
    id: _root

    property ActionNodeModel node
    property MapToVjoyModel action

    implicitHeight: _content.height


    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        VJoySelector {
            vjoyInputType: inputBinding.behavior
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
                    checked: _root.action.axisMode == "absolute"

                    onCheckedChanged: {
                        _root.action.axisMode = "absolute"
                    }
                }
                RadioButton {
                    id: _relativeMode
                    text: "Relative"
                    checked: _root.action.axisMode == "relative"

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
                    realValue: 1.0
                    stepSize: 0.1

                    onRealValueModified: function() {
                        _root.action.axisScaling = realValue
                    }
                }
            }
        }
        // UI for a button input
        Loader {
            active: _root.action.vjoyInputType == "button"
            Layout.fillWidth: true

            sourceComponent: Row {
                Switch {
                    text: "Invert activation"
                    checked: _root.action.buttonInverted

                    onToggled: function()
                    {
                        _root.action.buttonInverted = checked
                    }
                }
            }
        }
    }
}