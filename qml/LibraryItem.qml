// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2019 Lionel Ott
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
import QtQml.Models 2.14
import QtQuick.Window 2.14

import QtQuick.Controls.Universal 2.14

import gremlin.ui.profile 1.0


Item {
    property ActionTree actionTree

    anchors.fill: parent

    Column {
        id: idLayout
        anchors.fill: parent
        spacing: 10

        Repeater {
            model: actionTree
            delegate: Rectangle {
                id: idBase

                implicitWidth: parent.width
                implicitHeight: {
                    if(idActionButton.checked) {
                        idActionHeader.height + idAction.height
                    } else {
                        idActionHeader.height
                    }
                }

                anchors.left: parent.left
                anchors.right: parent.right
                anchors.margins: 10

                Row {
                    id: idActionHeader

                    anchors.top: parent.top

                    spacing: 10

                    FoldButton {
                        id: idActionButton

                        icon.source: checked ? "../gfx/button_delete.png" : "../gfx/button_add.png"
                    }

                    Label {
                        id: idActionName

                        anchors.verticalCenter: idActionButton.verticalCenter
                        anchors.leftMargin: 10

                        text: model.name
                    }

                    Rectangle {
                        id: idSeparator

                        implicitHeight: 2
                        implicitWidth: idBase.width - idActionName.width - idActionButton.width - 2 * idActionHeader.spacing
                        anchors.verticalCenter: idActionButton.verticalCenter

                        color: idActionButton.background.color
                    }
                }

                Item
                {
                    id: idAction
                    width: parent.width
                    anchors.top: idActionHeader.bottom
                    visible: idActionButton.checked

                    Component.onCompleted: {
                        var component = Qt.createComponent(Qt.resolvedUrl(qml_path));
                        if (component) {
                            if (component.status == Component.Ready) {
                                var obj = component.createObject(
                                    idAction,
                                    {model: profile_data}
                                );

                                idAction.height = obj.height;
                                obj.anchors.left = idAction.left;
                                obj.anchors.right = idAction.right;
                                obj.anchors.leftMargin = 20 * (model.depth - 1);

                            } else if (component.status == Component.Error) {
                                console.log("Error loading component:", component.errorString());
                            }
                        }
                    }
                }
            }
        } // Repeater
    }
}