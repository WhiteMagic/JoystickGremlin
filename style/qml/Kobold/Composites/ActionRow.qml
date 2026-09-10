// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Kobold.Controls
import Kobold.Foundation

// An action's row showing general action information and control actions. The action
// icon acts as the drag handle for the entire action.
Item {
    id: root

    // Variables storing the action's state.
    property bool expanded: true
    property string iconPath: ""
    property string name: ""
    property bool showTriggerMode: false
    property bool activateOnPress: false
    property bool activateOnRelease: false
    property bool hasError: false
    property string errorHint: ""
    property int depth: 0

    // Reference to the action the row controls. Required for the drag & drop system.
    property Item dragTarget: null
    readonly property alias dragActive: _dragArea.drag.active

    // Signals emitted to change and synchronize the action's state.
    signal toggleExpandedRequested()
    signal nameEdited(string text)
    signal activateOnPressEdited(bool value)
    signal activateOnReleaseEdited(bool value)
    signal removeRequested()
    signal dropRequested()

    implicitHeight: Metrics.rowAction
    implicitWidth: _row.implicitWidth

    RowLayout {
        id: _row

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        spacing: Metrics.gapS

        // Toggles the action between collapsed and expanded state.
        ToolButton {
            icon.name: "chevron-down"
            rotation: root.expanded ? 0 : -90

            onClicked: { root.toggleExpandedRequested() }
        }

        // Icon visually indicating the type of action.
        Image {
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

                // Handle dropping of the action, resolving the drag & drop interaction.
                onReleased: {
                    if (_dragArea.drag.active) {
                        root.dropRequested()
                    }
                }
            }
        }

        // Action name field, shows an editable textfield on hover.
        Item {
            Layout.fillWidth: true
            Layout.minimumWidth: Metrics.controlHeight * 4
            implicitHeight: Metrics.controlHeight

            HoverHandler {
                id: _nameHover
            }

            Rectangle {
                anchors.fill: parent
                radius: Metrics.radius
                color: _nameHover.hovered ? Theme.bgAlt : "transparent"
                border.width: Metrics.hairline
                border.color: _nameHover.hovered ? Theme.line : "transparent"
            }

            TextInput {
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

                onEditingFinished: { root.nameEdited(text) }
            }
        }

        ActivationToggle {
            visible: root.showTriggerMode

            pressChecked: { root.activateOnPress }
            releaseChecked: { root.activateOnRelease }

            onPressCheckedEdited: (value) => { root.activateOnPressEdited(value) }
            onReleaseCheckedEdited: (value) => { root.activateOnReleaseEdited(value) }
        }

        AppIcon {
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
            onClicked: { root.removeRequested() }
        }
    }
}
