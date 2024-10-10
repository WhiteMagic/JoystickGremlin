// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2023 Lionel Ott
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
import QtQuick.Templates as T
import QtQuick.Controls.Universal


Item {
    id: indicator

    implicitWidth: control.contentItem.font.pixelSize * 2.2
    implicitHeight: control.contentItem.font.pixelSize

    property T.AbstractButton control


    Rectangle {
        id: slot

        width: parent.width
        height: parent.height

        radius: height / 2 //10
        color: !indicator.control.enabled ? "transparent" :
                indicator.control.pressed ? indicator.control.Universal.baseMediumColor :
                indicator.control.checked ? indicator.control.Universal.accent : "transparent"
        border.color: !indicator.control.enabled ? indicator.control.Universal.baseLowColor :
                       indicator.control.checked && !indicator.control.pressed ? indicator.control.Universal.accent :
                       indicator.control.hovered && !indicator.control.checked && !indicator.control.pressed ? indicator.control.Universal.baseHighColor : indicator.control.Universal.baseMediumColor
        opacity: enabled && indicator.control.hovered && indicator.control.checked && !indicator.control.pressed ? (indicator.control.Universal.theme === Universal.Light ? 0.7 : 0.9) : 1.0
        border.width: height < 20 ? 1 : 2
    }

    Rectangle {
        id: circle

        width: 0.6 * slot.height //10
        height: 0.6 * slot.height //10
        radius: height / 2 //5

        color: !indicator.control.enabled ? indicator.control.Universal.baseLowColor :
                indicator.control.pressed || indicator.control.checked ? indicator.control.Universal.chromeWhiteColor :
                indicator.control.hovered && !indicator.control.checked ? indicator.control.Universal.baseHighColor : indicator.control.Universal.baseMediumHighColor

        x: indicator.control.visualPosition < 0.5 ? width / 2 : parent.width - 1.5 * width
        y: (parent.height - height) / 2

        Behavior on x {
            enabled: !indicator.control.pressed
            SmoothedAnimation { velocity: 200 }
        }
    }
}