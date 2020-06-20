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

import gremlin.ui.profile 1.0


Item {
    id: idRoot

    property ActionConfigurationModel action

    anchors.left: parent.left
    anchors.right: parent.right
    anchors.margins: 10

    height: idGeneralHeader.height + idBehaviourControls.height

    // General header
    Rectangle {
        id: idGeneralHeader

        anchors.left: parent.left
        anchors.right: parent.right

        height: 40

        color: Universal.background

        TextField {
            id: idDescription

            placeholderText: "Description"
            text: "" != action.description ? action.description : null

            anchors.left: idGeneralHeader.left
            anchors.right: idBehaviour.left
            anchors.verticalCenter: idBehaviour.verticalCenter

            onTextChanged: {
                action.description = text
            }
        }

        InputBehaviour {
            id: idBehaviour

            actionConfiguration: idRoot.action

            anchors.right: idHeaderRemove.left
        }

        Button {
            id: idHeaderRemove

            text: "X"
            anchors.right: idGeneralHeader.right
        }
    }

    // Behaviour controls header portion
    Item {
        id: idBehaviourControls

        anchors.top: idGeneralHeader.bottom
        anchors.left: parent.left
        anchors.right: parent.right

        height: idBehaviourAxisButton.active ? idBehaviourAxisButton.height : 0 +
                idBehaviourHatButton.active ? idBehaviourHatButton.height : 0

        // UI for a physical axis behaving as a button
        Loader {
            id: idBehaviourAxisButton

            active: action.behaviour == "button" && action.inputType == "axis"

            sourceComponent: Row {
                spacing: 10

                Label {
                    anchors.verticalCenter: idAxisRange.verticalCenter
                    text: "Activate between"
                }
                NumericalRangeSlider {
                    id: idAxisRange

                    from: -1.0
                    to: 1.0
                    firstValue: action.virtualButton.lowerLimit
                    secondValue: action.virtualButton.upperLimit
                    stepSize: 0.1
                    decimals: 3

                    onFirstValueChanged: {
                        action.virtualButton.lowerLimit = firstValue
                    }
                    onSecondValueChanged: {
                        action.virtualButton.upperLimit = secondValue
                    }
                }
                Label {
                    anchors.verticalCenter: idAxisRange.verticalCenter
                    text: "when entered from"
                }
                ComboBox {
                    model: ["Anywhere", "Above", "Below"]

                    // Select the correct entry
                    Component.onCompleted: {
                        currentIndex = find(
                            action.virtualButton.direction,
                            Qt.MatchFixedString
                        )
                    }

                    // TODO: Figure out the best way to handle initialization
                    //       without overwriting model values
                    //onCurrentTextChanged: {
                    onActivated: {
                        action.virtualButton.direction = currentText
                    }
                }
            }
        }

        // UI for a physical hat behaving as a button
        Loader {
            id: idBehaviourHatButton

            active: action.behaviour == "button" && action.inputType == "hat"

            sourceComponent: Row {
                spacing: 10
                height: 40

                HatDirectionSelector {
                    virtualButton: action.virtualButton
                }
            }
        }
    }
}