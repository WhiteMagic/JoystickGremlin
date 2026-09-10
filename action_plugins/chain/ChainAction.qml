// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Composites
import Kobold.Foundation


ColumnLayout {
    id: root

    required property ChainModel action

    spacing: Metrics.gapM

    RowLayout {
        spacing: Metrics.gapM

        Label {
            text: "Timeout (sec)"
        }

        DoubleSpinBox {
            from: 0
            to: 3600
            stepSize: 5
            decimals: 1
            value: root.action.timeout

            onValueModified: { root.action.timeout = value }
        }

        Spacer {}

        Button {
            text: "Add chain sequence"

            onClicked: { root.action.addSequence() }
        }
    }

    Repeater {
        model: root.action.chainCount

        delegate: ColumnLayout {
            id: _sequence

            required property int index

            Layout.fillWidth: true
            spacing: Metrics.gapS

            RowLayout {
                Layout.fillWidth: true
                spacing: Metrics.gapM

                SlotHeader {
                    Layout.fillWidth: true

                    label: "Sequence " + (_sequence.index + 1)
                    actionNames: root.action.compatibleActions

                    onActionRequested: (name) => {
                        root.action.appendAction(name, _sequence.index.toString())
                    }
                }

                ToolButton {
                    icon.name: "delete"

                    onClicked: { root.action.removeSequence(_sequence.index) }
                }
            }

            ActionList {
                Layout.fillWidth: true

                containerOwner: root.action
                containerName: _sequence.index.toString()
            }
        }
    }
}
