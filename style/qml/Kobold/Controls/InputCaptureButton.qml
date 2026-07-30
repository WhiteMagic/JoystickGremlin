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
Item {
    id: root

    property alias eventTypes: _listener.eventTypes
    property alias multipleInputs: _listener.multipleInputs
    property alias text: _label.text
    property var callback

    implicitWidth: _row.implicitWidth
    implicitHeight: Metrics.ctrlH

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
                width: contentWidth > 500 ? 500 : contentWidth + 20
                visible: _hoverHandler.hovered
                delay: 500
            }

            HoverHandler {
                id: _hoverHandler
                acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
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
