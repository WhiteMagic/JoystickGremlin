// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import QtQml.StateMachine as DSM

import Gremlin.Util
import Gremlin.Compact as Compact


Item {
    id: _root

    property alias eventTypes: _listener.eventTypes
    property alias multipleInputs: _listener.multipleInputs
    property alias text: _name.text
    property var callback

    implicitWidth: _button.implicitWidth
    implicitHeight: _button.implicitHeight

    // Underlying input listener model.
    InputListenerModel {
        id: _listener

        onListeningTerminated: function(inputs) {
            _root.callback(inputs)
        }
    }

    // State machine managing the input listener model setup and operational
    // modes.
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
        id: _button

        anchors.left: parent.left
        anchors.right: parent.right

        Compact.RecordButton {
            onClicked: () => { _popup.open() }
        }

        Label {
            id: _name

            Layout.fillWidth: true
            text: "Record Inputs"

            ToolTip {
                text: _name.text
                // Set an upper width of the tooltip to force word wrap on
                // long description texts.
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

        dim: true
        modal: true
        focus: true
        closePolicy: Popup.NoAutoClose

        // Overlay display
        ColumnLayout {
            id: _layout
            anchors.fill: parent

            RowLayout {
                Label {
                    text: "Waiting for user input. Hold ESC to abort."
                }
                Label {
                    text: _listener.currentInput
                }
            }
        }
    }
}