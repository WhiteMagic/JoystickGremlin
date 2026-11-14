// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Kobold.Composites
import Kobold.Controls
import Kobold.Foundation


ColumnLayout {
    id: root

    required property VirtualButtonModel action

    spacing: Metrics.gapM

    RowLayout {
        visible: root.action.parentBehavior === "axis"
        spacing: Metrics.gapM

        Label {
            text: "Activate between"
        }

        NumericRangeSlider {
            objectName: "virtualButtonRangeSlider"

            from: -1.0
            to: 1.0
            stepSize: 0.1
            decimals: 3
            firstValue: root.action.lowerLimit
            secondValue: root.action.upperLimit

            onFirstValueEdited: (value) => { root.action.lowerLimit = value }
            onSecondValueEdited: (value) => { root.action.upperLimit = value }
        }

        Label {
            text: "when entered from"
        }

        ComboBox {
            objectName: "virtualButtonDirectionCombo"

            model: ["Anywhere", "Above", "Below"]

            Component.onCompleted: () => {
                currentIndex = find(root.action.direction, Qt.MatchFixedString)
            }

            onActivated: (index) => { root.action.direction = currentText }
        }
    }

    RowLayout {
        visible: root.action.parentBehavior === "hat"
        spacing: Metrics.gapM

        Label {
            text: "Activate on"
        }

        HatDirectionToggle {
            objectName: "virtualButtonHatToggle"

            north: root.action.hatDirections.hatNorth
            northEast: root.action.hatDirections.hatNorthEast
            east: root.action.hatDirections.hatEast
            southEast: root.action.hatDirections.hatSouthEast
            south: root.action.hatDirections.hatSouth
            southWest: root.action.hatDirections.hatSouthWest
            west: root.action.hatDirections.hatWest
            northWest: root.action.hatDirections.hatNorthWest

            onNorthEdited: (value) => { root.action.hatDirections.hatNorth = value }
            onNorthEastEdited: (value) => { root.action.hatDirections.hatNorthEast = value }
            onEastEdited: (value) => { root.action.hatDirections.hatEast = value }
            onSouthEastEdited: (value) => { root.action.hatDirections.hatSouthEast = value }
            onSouthEdited: (value) => { root.action.hatDirections.hatSouth = value }
            onSouthWestEdited: (value) => { root.action.hatDirections.hatSouthWest = value }
            onWestEdited: (value) => { root.action.hatDirections.hatWest = value }
            onNorthWestEdited: (value) => { root.action.hatDirections.hatNorthWest = value }
        }
    }

    SlotHeader {
        Layout.fillWidth: true

        label: "Actions"
        actionNames: root.action.compatibleActions

        onActionRequested: (name) => { root.action.appendAction(name, "children") }
    }

    ActionList {
        Layout.fillWidth: true

        containerOwner: root.action
        containerName: "children"
    }
}
