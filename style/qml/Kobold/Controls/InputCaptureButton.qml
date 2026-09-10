// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQml.StateMachine as DSM
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Util
import Kobold.Foundation

// UI element triggering the recording of user inputs. Upon pressing of the button a
// popup appears providing information and feedback. The two available stylings differ
// in their background only:
// - ghost: no chrome at rest, an edge on hover
// - bordered: an ordinary button fill with a border
ToolButton {
    id: control

    // Options used to configure the recording behavior.
    property alias eventTypes: _listener.eventTypes
    property alias multipleInputs: _listener.multipleInputs
    property var callback

    // Style selection, "ghost" or "bordered". The background color of the button can
    // also be configured.
    property string variant: "ghost"
    property color fillColor: Theme.bgAlt

    readonly property bool bordered: variant === "bordered"
    readonly property bool ghostActive: !bordered && (hovered || down)

    text: "Record Inputs"

    // Setting icon.name would collapse the style's implicitWidth to a square, the icon
    // is part of the contentItem instead.
    implicitHeight: Metrics.controlHeight
    implicitWidth: leftPadding + implicitContentWidth + rightPadding

    // Adjust dimensions to allow icon and borders to be shown.
    leftPadding: bordered ? Metrics.gapM : Metrics.gapS
    rightPadding: bordered ? Metrics.gapM : Metrics.gapS
    topPadding: 0
    bottomPadding: 0

    onClicked: { _popup.open() }

    contentItem: RowLayout {
        spacing: Metrics.gapM

        Spacer {}

        AppIcon {
            Layout.alignment: Qt.AlignVCenter
            name: "assign"
            role: control.enabled ? "fg" : "fgDisabled"
        }

        Label {
            id: _label

            Layout.fillHeight: true
            text: control.text
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter

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

        Spacer {}
    }

    // The only place the variant is read.
    background: Rectangle {
        radius: Metrics.radius
        color: !control.bordered ? "transparent"
             : !control.enabled  ? Theme.bgAlt
             : control.down      ? Theme.bgSelected
             : control.hovered   ? Theme.bgHover
             :                     control.fillColor
        border.width: Metrics.hairline
        border.color: control.bordered || control.ghostActive ? Theme.line : "transparent"

        Rectangle {
            visible: control.visualFocus
            anchors.fill: parent
            anchors.margins: -2
            radius: parent.radius
            color: "transparent"
            border.width: 2
            border.color: Theme.accent
        }
    }

    // Model responsible to handle the actual user input capture.
    InputListenerModel {
        id: _listener

        onListeningTerminated: function(inputs) {
            control.callback(inputs)
        }
    }

    // State machine driving the recording and popup visibility.
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

    // Popup that appears when user input recording is active.
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
