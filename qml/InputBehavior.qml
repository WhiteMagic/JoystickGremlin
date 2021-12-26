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


import QtQuick
import QtQuick.Controls

import Gremlin.Profile


Item {
    id: _root

    property InputItemBindingModel inputBinding

    width: idContent.width
    height: idContent.height

    Row {
        id: idContent

        Loader {
            active: _root.inputBinding.inputType == "button"
            sourceComponent: RadioButton {
                visible: false
            }
        }

        Loader {
            active: _root.inputBinding.inputType != "button"

            sourceComponent: Row {
                Label {
                    id: idBehavior

                    leftPadding: 20
                    text: "Treat as"

                    anchors.verticalCenter: idBehaviorButton.verticalCenter
                }

                RadioButton {
                    id: idBehaviorButton

                    text: "Button"

                    checked: _root.inputBinding.behavior == "button"
                    onClicked: {
                        _root.inputBinding.behavior = "button"
                    }
                }

                Loader {
                    active: _root.inputBinding.inputType == "axis"
                    sourceComponent: RadioButton {
                        id: idBehaviorAxis

                        text: "Axis"

                        checked: _root.inputBinding.behavior == "axis"
                        onClicked: {
                            _root.inputBinding.behavior = "axis"
                        }
                    }
                }
                Loader {
                    active: _root.inputBinding.inputType == "hat"
                    sourceComponent: RadioButton {
                        id: idBehaviorHat

                        text: "Hat"

                        checked: _root.inputBinding.behavior == "hat"
                        onClicked: {
                            _root.inputBinding.behavior = "hat"
                        }
                    }
                }
            }
        }
    }
}