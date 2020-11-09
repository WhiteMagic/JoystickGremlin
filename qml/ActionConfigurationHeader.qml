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
import QtQuick.Layouts 1.14

import QtQuick.Controls.Universal 2.14

import gremlin.ui.profile 1.0


Item {
    id: _root

    property ActionTreeModel actionTree

    height: _generalHeader.height + _behaviourAxisButton.height + _behaviourHatButton.height


    // Content
    Column {
        id: _layout

        // Default header components visible with every input
        Row {
            id: _generalHeader

            TextField {
                id: _description

                width: _root.width - _behaviour.width - _headerRemove.width

                placeholderText: "Description"
                text: "" != actionTree.description ? actionTree.description : null

                onTextChanged: {
                    actionTree.description = text
                }
            }

            InputBehaviour {
                id: _behaviour

                actionTree: _root.actionTree
            }

            Button {
                id: _headerRemove

                icon.source: "../gfx/close.png"
            }
        }

        // UI for a physical axis behaving as a button
        Loader {
            id: _behaviourAxisButton

            active: actionTree.behaviour == "button" && actionTree.inputType == "axis"
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
                    firstValue: actionTree.virtualButton.lowerLimit
                    secondValue: actionTree.virtualButton.upperLimit
                    stepSize: 0.1
                    decimals: 3

                    onFirstValueChanged: {
                        actionTree.virtualButton.lowerLimit = firstValue
                    }
                    onSecondValueChanged: {
                        actionTree.virtualButton.upperLimit = secondValue
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
                            actionTree.virtualButton.direction,
                            Qt.MatchFixedString
                        )
                    }

                    // TODO: Figure out the best way to handle initialization
                    //       without overwriting model values
                    //onCurrentTextChanged: {
                    onActivated: {
                        actionTree.virtualButton.direction = currentText
                    }
                }
            }
        }

        // UI for a physical hat behaving as a button
        Loader {
            id: _behaviourHatButton

            active: actionTree.behaviour == "button" && actionTree.inputType == "hat"
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

                    virtualButton: actionTree.virtualButton
                }
            }
        }
    }


    // Fill the entire widget with a backgrund color
    Rectangle {
        color: Universal.baseMediumLowColor

        z: -1
        anchors.fill: _layout
    }
}