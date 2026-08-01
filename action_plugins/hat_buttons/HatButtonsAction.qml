// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Composites
import Kobold.Foundation


// Body only -- no chevron, header, name field, guide or indent, those are the core's.
ColumnLayout {
    id: root

    required property HatButtonsModel action

    spacing: Metrics.gapM

    RowLayout {
        spacing: Metrics.gapM

        Text {
            text: "Button mode"
            color: Theme.fg
            font.family: FontType.sans
            font.pixelSize: Metrics.textBody
        }

        RadioButton {
            text: "4 way"
            checked: root.action.buttonCount === 4

            onToggled: { root.action.buttonCount = 4 }
        }
        RadioButton {
            text: "8 way"
            checked: root.action.buttonCount === 8

            onToggled: { root.action.buttonCount = 8 }
        }
    }

    Repeater {
        model: root.action.buttonCount

        delegate: ColumnLayout {
            id: _direction

            readonly property string directionName: root.action.buttonName(index)

            Layout.fillWidth: true
            spacing: Metrics.gapS

            SlotHeader {
                Layout.fillWidth: true

                label: _direction.directionName
                actionNames: root.action.compatibleActions

                onActionRequested: (name) => {
                    root.action.appendAction(name, _direction.directionName)
                }
            }

            Repeater {
                model: root.action.getActions(_direction.directionName)

                delegate: ActionNode {
                    required property var modelData
                    required property int index

                    Layout.fillWidth: true

                    action: modelData
                    previousSibling: index > 0 ?
                        root.action.getActions(_direction.directionName)[index - 1] : null
                }
            }
        }
    }
}
