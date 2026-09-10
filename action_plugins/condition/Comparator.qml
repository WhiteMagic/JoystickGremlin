// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Kobold.Controls
import Kobold.Foundation


// Provides the UI element for a single condition row.
Item {
    id: root

    property var comparator: null

    implicitWidth: _content.implicitWidth
    implicitHeight: _content.implicitHeight

    RowLayout {
        id: _content

        spacing: Metrics.gapM

        Loader {
            active: root.comparator && root.comparator.typeName === "pressed"

            sourceComponent: ButtonStateSelector {
                isPressed: root.comparator.isPressed

                onStateModified: (isPressed) => { root.comparator.isPressed = isPressed }
            }
        }

        Loader {
            active: root.comparator && root.comparator.typeName === "range"

            sourceComponent: RowLayout {
                spacing: Metrics.gapM

                Label { text: "between" }

                DoubleSpinBox {
                    id: _lower

                    from: -1.0
                    to: _upper.value
                    stepSize: 0.05
                    decimals: Metrics.preciseDecimalPlaces
                    value: root.comparator.lowerLimit

                    onValueModified: { root.comparator.lowerLimit = value }
                }

                Label { text: "and" }

                DoubleSpinBox {
                    id: _upper

                    from: _lower.value
                    to: 1.0
                    stepSize: 0.05
                    decimals: Metrics.preciseDecimalPlaces
                    value: root.comparator.upperLimit

                    onValueModified: { root.comparator.upperLimit = value }
                }
            }
        }

        Loader {
            active: root.comparator && root.comparator.typeName === "direction"

            sourceComponent: HatDirectionToggle {
                north: root.comparator.model.hatNorth
                northEast: root.comparator.model.hatNorthEast
                east: root.comparator.model.hatEast
                southEast: root.comparator.model.hatSouthEast
                south: root.comparator.model.hatSouth
                southWest: root.comparator.model.hatSouthWest
                west: root.comparator.model.hatWest
                northWest: root.comparator.model.hatNorthWest

                onNorthEdited: (value) => { root.comparator.model.hatNorth = value }
                onNorthEastEdited: (value) => { root.comparator.model.hatNorthEast = value }
                onEastEdited: (value) => { root.comparator.model.hatEast = value }
                onSouthEastEdited: (value) => { root.comparator.model.hatSouthEast = value }
                onSouthEdited: (value) => { root.comparator.model.hatSouth = value }
                onSouthWestEdited: (value) => { root.comparator.model.hatSouthWest = value }
                onWestEdited: (value) => { root.comparator.model.hatWest = value }
                onNorthWestEdited: (value) => { root.comparator.model.hatNorthWest = value }
            }
        }
    }
}
