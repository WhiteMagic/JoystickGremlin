// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2020 Lionel Ott
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


import QtQuick 2.14
import QtQuick.Controls 2.14

import gremlin.ui.profile 1.0


Item {
    id: _root

    property ActionTreeModel actionTree

    width: idContent.width
    height: idContent.height

    Row {
        id: idContent

        Loader {
            active: _root.actionTree.inputType == "button"
            sourceComponent: RadioButton {
                visible: false
            }
        }

        Loader {
            active: _root.actionTree.inputType != "button"

            sourceComponent: Row {
                Label {
                    id: idBehaviour

                    leftPadding: 20
                    text: "Treat as"

                    anchors.verticalCenter: idBehaviourButton.verticalCenter
                }

                RadioButton {
                    id: idBehaviourButton

                    text: "Button"

                    checked: _root.actionTree.behaviour == "button"
                    onClicked: {
                        _root.actionTree.behaviour = "button"
                    }
                }

                Loader {
                    active: _root.actionTree.inputType == "axis"
                    sourceComponent: RadioButton {
                        id: idBehaviourAxis

                        text: "Axis"

                        checked: _root.actionTree.behaviour == "axis"
                        onClicked: {
                            _root.actionTree.behaviour = "axis"
                        }
                    }
                }
                Loader {
                    active: _root.actionTree.inputType == "hat"
                    sourceComponent: RadioButton {
                        id: idBehaviourHat

                        text: "Hat"

                        checked: _root.actionTree.behaviour == "hat"
                        onClicked: {
                            _root.actionTree.behaviour = "hat"
                        }
                    }
                }
            }
        }
    }
}