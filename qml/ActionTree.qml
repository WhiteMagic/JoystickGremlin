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
import QtQuick.Window 2.14
import QtQml.Models 2.14

import QtQuick.Controls.Universal 2.14

import gremlin.ui.profile 1.0


Item {
    id: _root

    property ActionTreeModel actionTree

    // anchors.left: parent.left
    // anchors.right: parent.right
    // anchors.rightMargin: 10
    // height: _header.height + _headerBorder.height + _action.height +
    //     _actionSelector.height
    // height: _header.height
    // width: _header.width

    height: _layout.height

    // Content
    Column {
        id: _layout

        anchors.left: _root.left
        anchors.right: _root.right
        anchors.leftMargin: 10
        anchors.rightMargin: 20


        // +------------------------------------------------------------------------
        // | Header
        // +------------------------------------------------------------------------
        ActionConfigurationHeader {
            id: _header

            anchors.left: parent.left
            anchors.right: parent.right

            actionTree: _root.actionTree
        }

        // BottomBorder {}


// General header
        // Rectangle {
        //     id: _generalHeader

        //     Layout.fillWidth: true
            
        //     implicitHeight: Math.max(_description.height, _behaviour.height, _headerRemove.height)

        //     color: Universal.background

        //     TextField {
        //         id: _description

        //         placeholderText: "Description"
        //         text: "" != _root.actionTree.description ? _root.actionTree.description : null

        //         anchors.left: _generalHeader.left
        //         anchors.right: _behaviour.left
        //         anchors.verticalCenter: _behaviour.verticalCenter

        //         onTextChanged: {
        //             _root.actionTree.description = text
        //         }
        //     }

        //     InputBehaviour {
        //         id: _behaviour

        //         actionTree: _root.actionTree

        //         anchors.right: _headerRemove.left
        //     }

        //     Button {
        //         id: _headerRemove

        //         icon.source: "../gfx/close.png"
        //         anchors.right: _generalHeader.right
        //     }
        // }

        // // Behaviour controls header portion
        // Item {
        //     id: _behaviourControls

        //     Layout.fillWidth: true
        //     implicitHeight: Math.max(_behaviourAxisButton.height, _behaviourHatButton.height)
        //     // height: _behaviourAxisButton.active ? _behaviourAxisButton.height : 0 +
        //     //         _behaviourHatButton.active ? _behaviourHatButton.sourceComponent.height : 0


        //     // UI for a physical axis behaving as a button
        //     Loader {
        //         id: _behaviourAxisButton

        //         active: _root.actionTree.behaviour == "button" && _root.actionTree.inputType == "axis"
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
        //                 firstValue: _root.actionTree.virtualButton.lowerLimit
        //                 secondValue: _root.actionTree.virtualButton.upperLimit
        //                 stepSize: 0.1
        //                 decimals: 3

        //                 onFirstValueChanged: {
        //                     _root.actionTree.virtualButton.lowerLimit = firstValue
        //                 }
        //                 onSecondValueChanged: {
        //                     _root.actionTree.virtualButton.upperLimit = secondValue
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
        //                         _root.actionTree.virtualButton.direction,
        //                         Qt.MatchFixedString
        //                     )
        //                 }

        //                 // TODO: Figure out the best way to handle initialization
        //                 //       without overwriting model values
        //                 //onCurrentTextChanged: {
        //                 onActivated: {
        //                     _root.actionTree.virtualButton.direction = currentText
        //                 }
        //             }
        //         }
        //     }

        //     // UI for a physical hat behaving as a button
        //     Loader {
        //         id: _behaviourHatButton

        //         active: _root.actionTree.behaviour == "button" && _root.actionTree.inputType == "hat"

        //         sourceComponent: Row {
        //             spacing: 10
        //             height: 40

        //             HatDirectionSelector {
        //                 virtualButton: _root.actionTree.virtualButton
        //             }
        //         }
        //     }
        // }

        // Rectangle {
        //     Layout.fillWidth: true
        //     implicitHeight: 10

        //     color: Universal.background
        // }
        // Rectangle {
        //     Layout.fillWidth: true
        //     implicitHeight: 2

        //     color: Universal.accent
        // }



        // +------------------------------------------------------------------------
        // | Render the root action node
        // +------------------------------------------------------------------------
        // ActionNode {
        //     id: _action

        //     action: _root.actionTree.rootAction
        //     actionTree: _root.actionTree

        //     anchors.top: _headerBorder.bottom
        //     anchors.left: parent.left
        //     anchors.right: parent.right
        // }

        // Loader {
        //     id: _actionSelector

        //     anchors.top: _action.bottom
        //     anchors.left: parent.left
        //     anchors.leftMargin: 10

        //     active: actionTree.actionCount == 0

        //     sourceComponent: ActionSelector {
        //         actionTree: actionTree
        //     }
        // }
    }
} // Item