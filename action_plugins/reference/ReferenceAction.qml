// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Controls
import Kobold.Foundation


// Body only -- no chevron, header, name field, guide or indent, those are the core's.
ColumnLayout {
    id: root

    required property ReferenceModel action

    property LabelValueSelectionModel referencesModel: action.actions

    RowLayout {
        spacing: Metrics.gapM

        ComboBox {
            id: _selection

            Layout.fillWidth: true
            model: root.referencesModel
            textRole: "label"
            valueRole: "value"

            Component.onCompleted: () => {
                currentIndex = root.referencesModel.currentSelectionIndex
            }
            Connections {
                target: root.referencesModel
                function onSelectionChanged() {
                    _selection.currentIndex = root.referencesModel.currentSelectionIndex
                }
            }
            onActivated: () => {
                root.referencesModel.currentValue = currentValue
            }
        }

        ToolButton {
            icon.name: "share"

            onClicked: () => { root.action.referenceAction(root.referencesModel.currentValue) }
        }

        ToolButton {
            icon.name: "duplicate"

            onClicked: () => { root.action.duplicateAction(root.referencesModel.currentValue) }
        }
    }
}
