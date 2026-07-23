// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kobold.Foundation

// SPEC §8 action row (28px): [chevron][type icon][name][TriggerMode?][error?][remove].
// The type icon doubles as the drag handle -- there is no separate drag column. The name
// field's always-present transparent border (line + bgAlt on hover) is the app's one
// sanctioned R1 exception; nothing else on this row reacts to a row-wide hover -- each
// control answers for itself.
//
// Deliberately model-agnostic: plain properties/signals only, no ActionModel coupling, so
// a future caller (Phase 7) can wire it to real data without changing this file.
Item {
    id: root

    property bool expanded: true
    property string iconName: ""
    property string name: ""
    property bool showTriggerMode: false
    property bool activateOnPress: false
    property bool activateOnRelease: false
    property bool hasError: false
    property string errorHint: ""
    property int depth: 0

    signal toggleExpandedRequested()
    signal nameEdited(string text)
    signal activateOnPressEdited(bool value)
    signal activateOnReleaseEdited(bool value)
    signal removeRequested()
    signal dragRequested()

    implicitHeight: Metrics.rowAction
    implicitWidth: _row.implicitWidth

    RowLayout {
        id: _row

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        spacing: Metrics.gapS

        ToolButton {
            id: _chevron

            checkable: true
            checked: root.expanded
            icon.name: "chevron-down"
            rotation: checked ? 0 : -90

            onClicked: root.toggleExpandedRequested()
        }

        AppIcon {
            id: _typeIcon

            name: root.iconName
            role: "fg"

            MouseArea {
                id: _dragArea

                anchors.fill: parent
                cursorShape: Qt.OpenHandCursor
                onPressed: root.dragRequested()
            }
        }

        Item {
            id: _nameField

            Layout.fillWidth: true
            Layout.minimumWidth: Metrics.ctrlH * 4
            implicitHeight: Metrics.ctrlH

            readonly property bool hovered: _nameHover.hovered

            HoverHandler {
                id: _nameHover
            }

            Rectangle {
                anchors.fill: parent
                radius: Metrics.radius
                color: _nameField.hovered ? Theme.bgAlt : "transparent"
                border.width: Metrics.hairline
                // Always present -- reserved even at rest -- so nothing resizes on hover
                // (SPEC §8's one sanctioned R1 exception).
                border.color: _nameField.hovered ? Theme.line : "transparent"
            }

            TextInput {
                id: _nameInput

                anchors.fill: parent
                anchors.leftMargin: Metrics.gapS
                anchors.rightMargin: Metrics.gapS
                verticalAlignment: TextInput.AlignVCenter
                clip: true

                text: root.name
                color: Theme.fg
                font.family: FontType.sans
                font.pixelSize: Metrics.textBody
                selectByMouse: true

                onEditingFinished: root.nameEdited(text)
            }
        }

        ActivationToggle {
            visible: root.showTriggerMode

            pressChecked: root.activateOnPress
            releaseChecked: root.activateOnRelease

            onPressCheckedEdited: (value) => root.activateOnPressEdited(value)
            onReleaseCheckedEdited: (value) => root.activateOnReleaseEdited(value)
        }

        AppIcon {
            id: _errorIcon

            visible: root.hasError
            name: "error"
            role: "error"

            HoverHandler {
                id: _errorHover
            }

            ToolTip.visible: _errorHover.hovered && root.errorHint !== ""
            ToolTip.text: root.errorHint
        }

        ToolButton {
            icon.name: "delete"
            onClicked: root.removeRequested()
        }
    }
}
