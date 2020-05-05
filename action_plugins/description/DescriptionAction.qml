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
import QtQuick.Window 2.14

import QtQuick.Controls.Universal 2.14

import gremlin.plugins 1.0


Item {
    property DescriptionModel model

    height: Math.max(idLabel.height, idDescription.height)

    Label {
        id: idLabel
        text: "Description"

        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        anchors.margins: 10
    }
    TextField {
        id: idDescription

        anchors.left: idLabel.right
        anchors.right: parent.right
        anchors.margins: 10
        anchors.verticalCenter: parent.verticalCenter

        placeholderText: null != model ? null : "Enter description"
        text: model.description//null != model ? model.description : null
        selectByMouse: true

        onTextChanged: {
            model.description = text
        }
    }
}