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

    height: _generalHeader.height// + _behaviourControls.height

    Component.onCompleted: {
        console.log(width + " " + height + " | " + x + " " + y)
    }

    Row {
        id: _layout

        width: parent.width

        // General header
        Rectangle {
            id: _generalHeader
            
            height: Math.max(_description.height, _behaviour.height, _headerRemove.height)

            color: Universal.background

            TextField {
                id: _description

                placeholderText: "Description"
                text: "" != actionTree.description ? actionTree.description : null

                anchors.left: _generalHeader.left
                anchors.right: _behaviour.left
                anchors.verticalCenter: _behaviour.verticalCenter

                onTextChanged: {
                    actionTree.description = text
                }
            }

            InputBehaviour {
                id: _behaviour

                actionTree: _root.actionTree

                anchors.right: _headerRemove.left
            }

            Button {
                id: _headerRemove

                icon.source: "../gfx/close.png"
                anchors.right: _generalHeader.right
            }
        }

        // Behaviour controls header portion
        // Item {
        //     id: _behaviourControls

        //     Layout.fillWidth: true
        //     height: Math.max(_behaviourAxisButton.height, _behaviourHatButton.height)
        //     // height: _behaviourAxisButton.active ? _behaviourAxisButton.height : 0 +
        //     //         _behaviourHatButton.active ? _behaviourHatButton.sourceComponent.height : 0


        //     // UI for a physical axis behaving as a button
        //     Loader {
        //         id: _behaviourAxisButton

        //         active: actionTree.behaviour == "button" && actionTree.inputType == "axis"
        //         onActiveChanged: {
        //             visible: active

        //             height = 0
        //         }

        //         sourceComponent: Row {
        //             spacing: 10

        //             Label {
        //                 anchors.verticalCenter: _axisRange.verticalCenter
        //                 text: "Activate between"
        //             }
        //             NumericalRangeSlider {
        //                 id: _axisRange

        //                 from: -1.0
        //                 to: 1.0
        //                 firstValue: actionTree.virtualButton.lowerLimit
        //                 secondValue: actionTree.virtualButton.upperLimit
        //                 stepSize: 0.1
        //                 decimals: 3

        //                 onFirstValueChanged: {
        //                     actionTree.virtualButton.lowerLimit = firstValue
        //                 }
        //                 onSecondValueChanged: {
        //                     actionTree.virtualButton.upperLimit = secondValue
        //                 }
        //             }
        //             Label {
        //                 anchors.verticalCenter: _axisRange.verticalCenter
        //                 text: "when entered from"
        //             }
        //             ComboBox {
        //                 model: ["Anywhere", "Above", "Below"]

        //                 // Select the correct entry
        //                 Component.onCompleted: {
        //                     currentIndex = find(
        //                         actionTree.virtualButton.direction,
        //                         Qt.MatchFixedString
        //                     )
        //                 }

        //                 // TODO: Figure out the best way to handle initialization
        //                 //       without overwriting model values
        //                 //onCurrentTextChanged: {
        //                 onActivated: {
        //                     actionTree.virtualButton.direction = currentText
        //                 }
        //             }
        //         }
        //     }

        //     // UI for a physical hat behaving as a button
        //     Loader {
        //         id: _behaviourHatButton

        //         active: actionTree.behaviour == "button" && actionTree.inputType == "hat"

        //         sourceComponent: Row {
        //             spacing: 10
        //             height: 40

        //             HatDirectionSelector {
        //                 virtualButton: actionTree.virtualButton
        //             }
        //         }
        //     }
        // }
    }
}