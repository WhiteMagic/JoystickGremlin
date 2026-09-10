// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Profile
import Kobold.Controls
import Kobold.Foundation

// UI element showing controls enabling to configure how an axis or hat is interpreted
// as a button.
Item {
    id: root

    property InputItemBindingModel inputBinding

    visible: _axisLoader.active || _hatLoader.active
    implicitHeight: Math.max(_axisLoader.height, _hatLoader.height)
    implicitWidth: Math.max(_axisLoader.width, _hatLoader.width)

    Loader {
        id: _axisLoader

        active: root.inputBinding &&
            root.inputBinding.behavior === "button" && root.inputBinding.inputType === "axis"
        visible: active

        sourceComponent: RowLayout {
            spacing: Metrics.gapM

            Label {
                text: "Activate between"
            }

            NumericRangeSlider {
                from: -1.0
                to: 1.0
                stepSize: 0.1
                decimals: 3
                firstValue: root.inputBinding.virtualButton.lowerLimit
                secondValue: root.inputBinding.virtualButton.upperLimit

                onFirstValueEdited: (value) => {
                    root.inputBinding.virtualButton.lowerLimit = value
                }
                onSecondValueEdited: (value) => {
                    root.inputBinding.virtualButton.upperLimit = value
                }
            }

            Label {
                text: "when entered from"
            }

            ComboBox {
                model: ["Anywhere", "Above", "Below"]

                Component.onCompleted: {
                    currentIndex = find(
                        root.inputBinding.virtualButton.direction, Qt.MatchFixedString
                    )
                }

                onActivated: {
                    root.inputBinding.virtualButton.direction = currentText
                }
            }
        }
    }

    Loader {
        id: _hatLoader

        active: root.inputBinding &&
            root.inputBinding.behavior === "button" &&
            root.inputBinding.inputType === "hat"
        visible: active

        sourceComponent: RowLayout {
            spacing: Metrics.gapM

            Label {
                text: "Activate on"
            }

            HatDirectionToggle {
                north: root.inputBinding.virtualButton.hatNorth
                northEast: root.inputBinding.virtualButton.hatNorthEast
                east: root.inputBinding.virtualButton.hatEast
                southEast: root.inputBinding.virtualButton.hatSouthEast
                south: root.inputBinding.virtualButton.hatSouth
                southWest: root.inputBinding.virtualButton.hatSouthWest
                west: root.inputBinding.virtualButton.hatWest
                northWest: root.inputBinding.virtualButton.hatNorthWest

                onNorthEdited: (value) => {
                    root.inputBinding.virtualButton.hatNorth = value
                }
                onNorthEastEdited: (value) => {
                    root.inputBinding.virtualButton.hatNorthEast = value
                }
                onEastEdited: (value) => {
                    root.inputBinding.virtualButton.hatEast = value
                }
                onSouthEastEdited: (value) => {
                    root.inputBinding.virtualButton.hatSouthEast = value
                }
                onSouthEdited: (value) => {
                    root.inputBinding.virtualButton.hatSouth = value
                }
                onSouthWestEdited: (value) => {
                    root.inputBinding.virtualButton.hatSouthWest = value
                }
                onWestEdited: (value) => {
                    root.inputBinding.virtualButton.hatWest = value
                }
                onNorthWestEdited: (value) => {
                    root.inputBinding.virtualButton.hatNorthWest = value
                }
            }
        }
    }
}
