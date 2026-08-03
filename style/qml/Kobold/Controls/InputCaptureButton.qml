// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import QtQml.StateMachine as DSM

import Gremlin.Util
import Kobold.Foundation

// Replaces qml/InputListener.qml's Compact.RecordButton (gone) with a plain Kobold
// ToolButton, and its ad-hoc Popup body with the standard opaque bgAlt + 1px line
// popup treatment (R2: no shadow). The InputListenerModel/state-machine logic
// driving the actual capture is unchanged -- this is a reskin, not a rebuild.
//
// Two chrome variants share the same capture logic, same split AddActionMenuButton.qml
// uses for its ghost/bordered pair: "ghost" (default) is the original small icon + plain
// label, no chrome at rest; "bordered" is one obvious bordered push-button surface for
// standalone CTAs (e.g. a list's trailing "Add Key" button).
Item {
    id: root

    property alias eventTypes: _listener.eventTypes
    property alias multipleInputs: _listener.multipleInputs
    property alias text: _label.text
    property var callback
    property string variant: "ghost"
    // Bordered variant's own fill -- a caller on a bgAlt pane (e.g. KeyboardInputList) wants
    // the button raised to bg instead of blending into it.
    property color fillColor: Theme.bgAlt

    readonly property bool bordered: root.variant === "bordered"

    implicitWidth: root.bordered ? _button.implicitWidth : _row.implicitWidth
    implicitHeight: Metrics.controlHeight

    InputListenerModel {
        id: _listener

        onListeningTerminated: function(inputs) {
            root.callback(inputs)
        }
    }

    DSM.StateMachine {
        id: _stateMachine

        initialState: disabled
        running: true

        DSM.State {
            id: disabled

            DSM.SignalTransition {
                targetState: enabled
                signal: _popup.aboutToShow
            }

            onEntered: function() {
                _listener.enabled = false
                _popup.close()
            }
        }

        DSM.State {
            id: enabled

            DSM.SignalTransition {
                targetState: disabled
                signal: _popup.closed
            }

            DSM.SignalTransition {
                targetState: disabled
                signal: _listener.listeningTerminated
            }

            onEntered: function() {
                _listener.enabled = true
            }
        }
    }

    RowLayout {
        id: _row

        visible: !root.bordered
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: Metrics.gapM

        ToolButton {
            icon.name: "assign"
            onClicked: () => { _popup.open() }
        }

        Text {
            id: _label

            Layout.fillWidth: true
            text: "Record Inputs"
            color: Theme.fg
            font.family: FontType.sans
            font.pixelSize: Metrics.textBody
            elide: Text.ElideRight

            ToolTip {
                text: _label.text
                width: Metrics.tooltipWidth(contentWidth)
                visible: _hoverHandler.hovered
                delay: 500
            }

            HoverHandler {
                id: _hoverHandler
                acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
            }
        }
    }

    // "bordered": whole surface is the click target, an ordinary bordered push-button
    // (see Kobold/Button.qml) with the icon folded into its contentItem instead of split
    // out as a separate icon-only ToolButton.
    ToolButton {
        id: _button

        visible: root.bordered
        anchors.left: parent.left
        anchors.right: parent.right

        text: root.text
        onClicked: () => { _popup.open() }

        // Item wrapper, not a bare RowLayout -- a RowLayout used directly as contentItem
        // keeps its own top-left-packed natural size instead of being vertically centered
        // by the control (see AddActionMenuButton.qml).
        contentItem: Item {
            implicitWidth: _buttonRow.implicitWidth
            implicitHeight: Metrics.controlHeight

            RowLayout {
                id: _buttonRow

                anchors.centerIn: parent
                spacing: Metrics.gapM

                AppIcon {
                    name: "assign"
                    role: _button.enabled ? "fg" : "fgDisabled"
                }

                Text {
                    text: _button.text
                    color: _button.enabled ? Theme.fg : Theme.fgDisabled
                    font.family: FontType.sans
                    font.pixelSize: Metrics.textBody
                    elide: Text.ElideRight
                }
            }
        }

        background: Rectangle {
            radius: Metrics.radius
            color: !_button.enabled ? Theme.bgAlt
                 : _button.down     ? Theme.bgSelected
                 : _button.hovered  ? Theme.bgHover
                 :                    root.fillColor
            border.width: Metrics.hairline
            border.color: Theme.line

            Rectangle {
                visible: _button.visualFocus
                anchors.fill: parent
                anchors.margins: -2
                radius: parent.radius
                color: "transparent"
                border.width: 2
                border.color: Theme.accent
            }
        }
    }

    Popup {
        id: _popup

        parent: Overlay.overlay
        anchors.centerIn: Overlay.overlay

        modal: true
        focus: true
        closePolicy: Popup.NoAutoClose

        background: Rectangle {
            color: Theme.bgAlt
            border.width: Metrics.hairline
            border.color: Theme.line
        }

        ColumnLayout {
            anchors.fill: parent
            spacing: Metrics.gapS

            Label {
                text: "Waiting for user input. Hold ESC to abort."
            }
            Label {
                text: _listener.currentInput
            }
        }
    }
}
