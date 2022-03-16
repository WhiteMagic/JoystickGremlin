// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2022 Lionel Ott
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.


import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import QtQml.StateMachine as DSM

import Gremlin.Util


Item {
    id: _root

    property alias eventTypes: _listener.eventTypes
    property alias multipleInputs: _listener.multipleInputs
    property var callback

    implicitHeight: _content.height
    implicitWidth: _content.width

    // Underlying input listener model
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

    // Main display
    RowLayout {
        id: _content
        
        Layout.fillWidth: true

        Label {
            text: "Input"
        }

        Label {
            text: "Stuff"
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
                        text: "Waiting for user input"
                    }
                    Label {
                        text: _listener.currentInput
                    }
                }
            }
        }

        Button {
            id: _button
            text: "Record Inputs"
            Layout.alignment: Qt.AlignRight

            onClicked: function()
            {
                _popup.open()                
            }
        }
    }



}