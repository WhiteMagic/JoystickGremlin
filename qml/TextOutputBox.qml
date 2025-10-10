// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2025 Lionel Ott
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
import QtQuick.Controls.Universal

Rectangle {
    id: root
    property alias text: _notificationLabel.text
    
    color: Universal.background
    border.color: Universal.accent

    Label {
        id: _notificationLabel
        anchors.fill: parent
        anchors.margins: 8
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}