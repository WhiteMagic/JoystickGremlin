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
    property ActionConfigurationModel actionConfiguration

    width: idContent.width
    height: idContent.height

    Row {
        id: idContent

        Loader {
            active: actionConfiguration.inputType == "button"
            sourceComponent: RadioButton {
                visible: false
            }
        }

        Loader {
            active: actionConfiguration.inputType != "button"

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

                    checked: actionConfiguration.behaviour == "button"
                    onClicked: {
                        actionConfiguration.behaviour = "button"
                    }
                }

                Loader {
                    active: actionConfiguration.inputType == "axis"
                    sourceComponent: RadioButton {
                        id: idBehaviourAxis

                        text: "Axis"

                        checked: actionConfiguration.behaviour == "axis"
                        onClicked: {
                            actionConfiguration.behaviour = "axis"
                        }
                    }
                }
                Loader {
                    active: actionConfiguration.inputType == "hat"
                    sourceComponent: RadioButton {
                        id: idBehaviourHat

                        text: "Hat"

                        checked: actionConfiguration.behaviour == "hat"
                        onClicked: {
                            actionConfiguration.behaviour = "hat"
                        }
                    }
                }
            }
        }
    }
}