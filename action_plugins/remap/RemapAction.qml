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
    id: idRoot

    property ActionTreeModel actionTree
    property RemapModel model

    //height: idVjoy.height
    //width: parent.width

    ColumnLayout {
        Item {
            VJoySelector {
                id: idVjoy

                anchors.left: parent.left

                inputType: model.inputType
                vjoyInputId: model.vjoyInputId
                vjoyDeviceId: model.vjoyDeviceId
                validTypes: [actionTree.behaviour]

                onVjoyInputIdChanged: { model.vjoyInputId = vjoyInputId }
                onVjoyDeviceIdChanged: { model.vjoyDeviceId = vjoyDeviceId }
                onInputTypeChanged: { model.inputType = inputType }
            }

            // UI for a physical axis behaving as an axis
            Row {
                anchors.left: idVjoy.right
                spacing: 10

                visible: actionTree.behaviour == "axis"

                Rectangle {
                    width: 10
                    height: 1
                }

                RadioButton {
                    text: "Absolute"
                    checked: true

                    onCheckedChanged: {
                        model.axisMode = "absolute"
                    }
                }
                RadioButton {
                    id: idRelativeMode
                    text: "Relative"

                    onCheckedChanged: {
                        model.axisMode = "relative"
                    }
                }

                Label {
                    text: "Scaling"
                    anchors.verticalCenter: parent.verticalCenter
                    visible: idRelativeMode.checked
                }

                FloatSpinBox {
                    id: idScaling

                    visible: idRelativeMode.checked
                    minValue: 0
                    maxValue: 100
                    value: 1
                    stepSize: 0.1

                    onValueChanged: {
                        model.axisScaling = value
                    }
                }
            }
        }
    }
}