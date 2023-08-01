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

import QtQuick.Controls.Universal

import Gremlin.Profile


Item {
    id: _root

    property InputItemBindingModel inputBinding
    property MouseArea dragHandleArea: _dragArea

    height: _generalHeader.height + _behaviorAxisButton.height +
        _behaviorHatButton.height
    z: -1

    // Content
    ColumnLayout {
        id: _layout

        anchors.left: parent.left
        anchors.right: parent.right

        // Default header components visible with every input
        RowLayout {
            id: _generalHeader

            IconButton {
                id: _handle

                font.pixelSize: 24
                horizontalPadding: -5
                text: Constants.verticalDrag

                // Drag handle mouse interaction area
                MouseArea {
                    id: _dragArea

                    anchors.fill: parent

                    drag.target: _handle
                    drag.axis: Drag.YAxis
                }
            }

            TextField {
                id: _description

                Layout.fillWidth: true

                placeholderText: "Description"
                text: "" != _root.inputBinding.description ?
                    _root.inputBinding.description : null

                onTextChanged: {
                    _root.inputBinding.description = text
                }
            }

            InputBehavior {
                id: _behavior

                inputBinding: _root.inputBinding
            }

            ActionSelector {
                Layout.alignment: Qt.AlignRight

                actionNode: _root.inputBinding.rootAction
                callback: function(x) { actionNode.appendAction(x, "children"); }
            }

            IconButton {
                id: _headerRemove

                text: Constants.remove
                font.pixelSize: 24

                onClicked: function()
                {
                    inputBinding.deleteActionSequence()
                }
            }
        }

        // UI for a physical axis behaving as a button
        Loader {
            id: _behaviorAxisButton

            active: _root.inputBinding.behavior == "button" &&
                 _root.inputBinding.inputType == "axis"
            onActiveChanged: {
                visible: active
                height = active ? item.contentHeight : 0
            }

            sourceComponent: Row {
                spacing: 10

                property int contentHeight: Math.max(
                    _axisLabel.height,
                    _axisRange.height,
                    _axisDirection.height
                )

                Label {
                    id: _axisLabel

                    anchors.verticalCenter: _axisRange.verticalCenter
                    text: "Activate between"
                }
                NumericalRangeSlider {
                    id: _axisRange

                    from: -1.0
                    to: 1.0
                    firstValue: _root.inputBinding.virtualButton.lowerLimit
                    secondValue: _root.inputBinding.virtualButton.upperLimit
                    stepSize: 0.1
                    decimals: 3

                    onFirstValueChanged: {
                        _root.inputBinding.virtualButton.lowerLimit = firstValue
                    }
                    onSecondValueChanged: {
                        _root.inputBinding.virtualButton.upperLimit = secondValue
                    }
                }
                Label {
                    anchors.verticalCenter: _axisRange.verticalCenter
                    text: "when entered from"
                }
                ComboBox {
                    id: _axisDirection

                    model: ["Anywhere", "Above", "Below"]

                    // Select the correct entry
                    Component.onCompleted: {
                        currentIndex = find(
                            _root.inputBinding.virtualButton.direction,
                            Qt.MatchFixedString
                        )
                    }

                    onActivated: {
                        _root.inputBinding.virtualButton.direction = currentText
                    }
                }
            }
        }

        // UI for a physical hat behaving as a button
        Loader {
            id: _behaviorHatButton

            active: _root.inputBinding.behavior == "button" &&
                _root.inputBinding.inputType == "hat"
            onActiveChanged: {
                visible: active
                height = active ? item.contentHeight : 0
            }

            sourceComponent: Row {
                property int contentHeight: Math.max(
                    _hatDirection.height,
                    _hatLabel.height
                )

                spacing: 10

                Label {
                    id: _hatLabel
                    anchors.verticalCenter: _hatDirection.verticalCenter
                    text: "Activate on"
                }
                HatDirectionSelector {
                    id: _hatDirection

                    virtualButton: _root.inputBinding.virtualButton
                }
            }
        }
    }
}