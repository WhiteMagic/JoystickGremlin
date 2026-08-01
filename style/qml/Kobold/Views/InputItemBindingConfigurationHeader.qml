// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Profile
import Kobold.Controls
import Kobold.Foundation
import "helpers.js" as Helpers

Item {
    id: _root

    property InputItemBindingModel inputBinding
    property InputItemModel inputItemModel
    property MouseArea dragHandleArea: _dragArea

    implicitHeight: _layout.implicitHeight

    ColumnLayout {
        id: _layout

        anchors.left: parent.left
        anchors.right: parent.right

        // Default header components visible with every input.
        RowLayout {
            id: _generalHeader

            Layout.fillWidth: true

            ToolButton {
                id: _handle

                icon.name: "grip"

                // Drag handle mouse interaction area.
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
                text: _root.inputBinding.rootAction ?
                    _root.inputBinding.rootAction.actionLabel : "Description"

                onTextEdited: () => {
                    _root.inputBinding.rootAction.actionLabel = text
                }
            }

            InputBehavior {
                id: _behavior

                inputBinding: _root.inputBinding
            }

            AddActionMenuButton {
                Layout.alignment: Qt.AlignRight

                variant: "bordered"
                model: _root.inputBinding.rootAction ?
                    _root.inputBinding.rootAction.compatibleActions : []

                onActionRequested: (name) => {
                    _root.inputBinding.rootAction.appendAction(name, "children")
                }
            }

            AppIcon {
                visible: _root.inputBinding.userFeedback.length > 0

                name: Helpers.determineHintIcon(_root.inputBinding.userFeedback)
                role: Helpers.determineHintRole(_root.inputBinding.userFeedback)

                HoverHandler {
                    onHoveredChanged: () => {
                        _hintsTooltip.parent = parent
                        _hintsTooltip.x = -_hintsTooltip.width - 5
                        _hintsTooltip.y = parent.height + 5
                        _hintsTooltip.hints = _root.inputBinding.userFeedback
                        _hintsTooltip.visible = hovered
                    }
                }
            }

            ToolButton {
                icon.name: "delete"

                onClicked: () => {
                    _root.inputItemModel.deleteActionSequnce(_root.inputBinding)
                }
            }
        }

        // UI for an axis behaving like a button.
        Loader {
            id: _behaviorAxisButton

            active: _root.inputBinding.behavior == "button" &&
                _root.inputBinding.inputType == "axis"
            visible: active

            sourceComponent: RowLayout {
                Label {
                    Layout.leftMargin: 20

                    text: "Activate between"
                }
                NumericRangeSlider {
                    from: -1.0
                    to: 1.0
                    firstValue: _root.inputBinding.virtualButton.lowerLimit
                    secondValue: _root.inputBinding.virtualButton.upperLimit
                    stepSize: 0.1
                    decimals: 3

                    onFirstValueEdited: (value) => {
                        _root.inputBinding.virtualButton.lowerLimit = value
                    }
                    onSecondValueEdited: (value) => {
                        _root.inputBinding.virtualButton.upperLimit = value
                    }
                }
                Label {
                    text: "when entered from"
                }
                ComboBox {
                    model: ["Anywhere", "Above", "Below"]

                    // Select the correct entry.
                    Component.onCompleted: () => {
                        currentIndex = find(
                            _root.inputBinding.virtualButton.direction,
                            Qt.MatchFixedString
                        )
                    }

                    onActivated: () => {
                        _root.inputBinding.virtualButton.direction = currentText
                    }
                }
            }
        }

        // UI for a hat behaving like a button.
        Loader {
            active: _root.inputBinding.behavior == "button" &&
                _root.inputBinding.inputType == "hat"
            visible: active

            sourceComponent: RowLayout {
                Label {
                    Layout.leftMargin: 20

                    text: "Activate on"
                }
                HatDirectionToggle {
                    north: _root.inputBinding.virtualButton.hatNorth
                    northEast: _root.inputBinding.virtualButton.hatNorthEast
                    east: _root.inputBinding.virtualButton.hatEast
                    southEast: _root.inputBinding.virtualButton.hatSouthEast
                    south: _root.inputBinding.virtualButton.hatSouth
                    southWest: _root.inputBinding.virtualButton.hatSouthWest
                    west: _root.inputBinding.virtualButton.hatWest
                    northWest: _root.inputBinding.virtualButton.hatNorthWest

                    onNorthEdited: (value) => { _root.inputBinding.virtualButton.hatNorth = value }
                    onNorthEastEdited: (value) => { _root.inputBinding.virtualButton.hatNorthEast = value }
                    onEastEdited: (value) => { _root.inputBinding.virtualButton.hatEast = value }
                    onSouthEastEdited: (value) => { _root.inputBinding.virtualButton.hatSouthEast = value }
                    onSouthEdited: (value) => { _root.inputBinding.virtualButton.hatSouth = value }
                    onSouthWestEdited: (value) => { _root.inputBinding.virtualButton.hatSouthWest = value }
                    onWestEdited: (value) => { _root.inputBinding.virtualButton.hatWest = value }
                    onNorthWestEdited: (value) => { _root.inputBinding.virtualButton.hatNorthWest = value }
                }
            }
        }
    }
}
