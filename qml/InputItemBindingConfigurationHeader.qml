// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts

import Gremlin.Profile
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

            IconButton {
                id: _handle

                font.pixelSize: 24
                horizontalPadding: -5
                text: bsi.icons.verticalDrag

                // Drag handle mouse interaction area.
                MouseArea {
                    id: _dragArea

                    anchors.fill: parent

                    drag.target: _handle
                    drag.axis: Drag.YAxis
                }
            }

            JGTextField {
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

            ActionSelector {
                Layout.alignment: Qt.AlignRight

                actionNode: _root.inputBinding.rootAction
                callback: (x) => { actionNode.appendAction(x, "children") }
            }

            Label {
                visible: _root.inputBinding.userFeedback.length > 0

                font.family: "bootstrap-icons"
                font.pixelSize: 24

                text: Helpers.determineHintIcon(_root.inputBinding.userFeedback)
                color: Helpers.determineHintColor(_root.inputBinding.userFeedback)

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

            IconButton {
                text: bsi.icons.remove
                font.pixelSize: 24

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
                NumericalRangeSlider {
                    from: -1.0
                    to: 1.0
                    firstValue: _root.inputBinding.virtualButton.lowerLimit
                    secondValue: _root.inputBinding.virtualButton.upperLimit
                    stepSize: 0.1
                    decimals: 3

                    onFirstValueChanged: () => {
                        _root.inputBinding.virtualButton.lowerLimit = firstValue
                    }
                    onSecondValueChanged: () => {
                        _root.inputBinding.virtualButton.upperLimit = secondValue
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
                HatDirectionSelector {
                    virtualButton: _root.inputBinding.virtualButton
                }
            }
        }
    }
}
