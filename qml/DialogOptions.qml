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

import Gremlin.Config


Window {
    minimumWidth: 900
    minimumHeight: 500

    title: "Options"

    ConfigSectionModel {
        id: _sectionModel
    }

    RowLayout {
        id: _root

        anchors.fill: parent

        ListView {
            id: _sectionView

            Layout.preferredWidth: 200
            Layout.fillHeight: true

            model: _sectionModel
            delegate: _sectionDelegate
        }

        ScrollView {
            Layout.fillHeight: true
            Layout.fillWidth: true

            ConfigGroup {
                id: _configGroup
            }
        }
    }

    Component {
        id: _sectionDelegate

        Button {
            id: _text

            required property int index
            required property string name
            required property ConfigGroupModel groupModel

            text: name

            height: 40
            width: _sectionView.width

            background: Row {
                Rectangle {
                    width: 5
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom

                    color: _sectionView.currentIndex == index ?
                        Universal.accent : Universal.background
                }
                Rectangle {
                    x: 5
                    width: parent.width - 5
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom

                    color: _sectionView.currentIndex == index ?
                        Universal.chromeMediumColor : Universal.background
                }
            }

            contentItem: Text {
                text: _text.text.replace(/\b\w/g, l => l.toUpperCase())
                font: _text.font
                horizontalAlignment: Text.AlignLeft
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
            }

            onClicked: function() {
                _sectionView.currentIndex = index
                _configGroup.groupModel = groupModel
            }
        }
    }
}