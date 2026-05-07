// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts

import Gremlin.Profile
import Gremlin.ActionPlugins
import "../../qml"


Item {
    id: _root

    property MapToVjoyModel action

    implicitHeight: _content.height


    RowLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        VJoySelector {
            validTypes: [_root.action.actionBehavior]

            // Propagate internal changes to the external interface.
            onSelectionChanged: (vjoyId, inputType, inputId) => {
                _root.action.vjoyDeviceId = vjoyId
                _root.action.vjoyInputType = inputType
                _root.action.vjoyInputId = inputId

            }

            Component.onCompleted: {
                initialize(
                    _root.action.vjoyDeviceId,
                    _root.action.actionBehavior,
                    _root.action.vjoyInputId
                )
            }
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
                    stepSize: 0.1
                    value: _root.action.axisScaling

                    onValueModified: (newValue) => {
                        _root.action.axisScaling = newValue
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
