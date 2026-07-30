// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kobold.Foundation
import Kobold.Controls

import Gremlin.Profile

// Ported from the axis/hat "virtual button" Loaders in the legacy
// qml/InputItemBindingConfigurationHeader.qml. Kept as its own sibling component rather than
// folded into BindingHeader.qml: this row isn't part of SPEC §8's binding-header grammar, it's
// the axis/hat activation-range UI, shown only when behavior === "button".
//
// Kept as Loaders (not a plain hidden Item), matching the legacy file's own laziness: the
// ComboBox's Component.onCompleted reads inputBinding.virtualButton.direction unconditionally,
// so it must not be instantiated before behavior/inputType are actually known.
Item {
    id: root

    property InputItemBindingModel inputBinding

    // Layouts only skip spacing around a row that's actually invisible -- an active-less
    // Item still costs a full spacing gap on each side even at 0 height, so this must track
    // the same condition as the two Loaders below, not just leave them empty.
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

            Text {
                text: "Activate between"
                color: Theme.fg
                font.family: FontType.sans
                font.pixelSize: Metrics.textBody
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

            Text {
                text: "when entered from"
                color: Theme.fg
                font.family: FontType.sans
                font.pixelSize: Metrics.textBody
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
            root.inputBinding.behavior === "button" && root.inputBinding.inputType === "hat"
        visible: active

        sourceComponent: RowLayout {
            spacing: Metrics.gapM

            Text {
                text: "Activate on"
                color: Theme.fg
                font.family: FontType.sans
                font.pixelSize: Metrics.textBody
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

                onNorthEdited: (value) => { root.inputBinding.virtualButton.hatNorth = value }
                onNorthEastEdited: (value) => {
                    root.inputBinding.virtualButton.hatNorthEast = value
                }
                onEastEdited: (value) => { root.inputBinding.virtualButton.hatEast = value }
                onSouthEastEdited: (value) => {
                    root.inputBinding.virtualButton.hatSouthEast = value
                }
                onSouthEdited: (value) => { root.inputBinding.virtualButton.hatSouth = value }
                onSouthWestEdited: (value) => {
                    root.inputBinding.virtualButton.hatSouthWest = value
                }
                onWestEdited: (value) => { root.inputBinding.virtualButton.hatWest = value }
                onNorthWestEdited: (value) => {
                    root.inputBinding.virtualButton.hatNorthWest = value
                }
            }
        }
    }
}
