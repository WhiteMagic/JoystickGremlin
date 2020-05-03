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
        spacing: 2

        Repeater {
            model: actionTree
            delegate: Item {
                id: idFactoryItem
                width: parent.width

                Component.onCompleted: {
                    var component = Qt.createComponent(Qt.resolvedUrl(qml_path));
                    if (component) {
                        if (component.status == Component.Ready) {
                            var obj = component.createObject(idFactoryItem, {model: profile_data});

                            idFactoryItem.height = obj.height;
                            obj.anchors.left = idFactoryItem.left;
                            obj.anchors.right = idFactoryItem.right;

                        } else if (component.status == Component.Error) {
                            console.log("Error loading component:", component.errorString());
                        }
                    }
                }
            }

        } // Repeater
    }
}