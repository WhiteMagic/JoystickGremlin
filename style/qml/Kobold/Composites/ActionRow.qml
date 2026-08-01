// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Kobold.Foundation
import Kobold.Controls

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
    property string iconPath: ""
    property string name: ""
    property bool showTriggerMode: false
    property bool activateOnPress: false
    property bool activateOnRelease: false
    property bool hasError: false
    property string errorHint: ""
    property int depth: 0
    // The Item that should actually move during a drag -- set by the caller (the row
    // itself has no opinion on what "the row" means to its parent's layout).
    property Item dragTarget: null
    // Exposed so the caller can drive `dragTarget.Drag.active` -- declaring
    // `drag.target` alone does not do that automatically.
    readonly property alias dragActive: _dragArea.drag.active

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

        // Stateless trigger, not checkable -- `expanded` is the caller's own property
        // (round-tripped explicitly through toggleExpandedRequested), not something a
        // checkable button's internal toggle state should own or fight over.
        ToolButton {
            id: _chevron

            icon.name: "chevron-down"
            rotation: root.expanded ? 0 : -90

            onClicked: root.toggleExpandedRequested()
        }

        // Plugin-authored icon, tinted to `fg` only (never a switchable role, unlike
        // AppIcon) via the dedicated `action-icon` image provider -- a separate
        // provider from AppIcon's `icon` one, since `root.iconPath` is a `file:///...`
        // URI onto an arbitrary plugin's icon.svg (core or user-authored), not a name
        // in the bundled :/style-icons/ set.
        Image {
            id: _typeIcon

            source: root.iconPath
                ? "image://action-icon/" + root.iconPath + "?c="
                    + Theme.fg.toString().slice(-6) + "&px=" + Metrics.icon
                : ""
            sourceSize.width: Metrics.icon
            sourceSize.height: Metrics.icon
            width: Metrics.icon
            height: Metrics.icon
            fillMode: Image.PreserveAspectFit
            smooth: true

            MouseArea {
                id: _dragArea

                anchors.fill: parent
                cursorShape: Qt.OpenHandCursor
                drag.target: root.dragTarget
                drag.axis: Drag.YAxis
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
