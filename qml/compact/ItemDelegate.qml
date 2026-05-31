// Copyright (C) 2017 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial
// Modified by Joystick Gremlin Contributors

import QtQuick
import QtQuick.Templates as T
import QtQuick.Controls.impl
import QtQuick.Controls.Universal

T.ItemDelegate {
    id: control

    implicitWidth: Math.max(implicitBackgroundWidth + leftInset + rightInset,
                            implicitContentWidth + leftPadding + rightPadding)
    implicitHeight: Math.max(implicitBackgroundHeight + topInset + bottomInset,
                             implicitContentHeight + topPadding + bottomPadding,
                             implicitIndicatorHeight + topPadding + bottomPadding)

    spacing: 8

    padding: 6
    topPadding: 4
    bottomPadding: 4

    icon.width: 16
    icon.height: 16
    icon.color: Color.transparent(Universal.foreground, enabled ? 1.0 : 0.2)
    font.pixelSize: 14

    contentItem: IconLabel {
        spacing: control.spacing
        mirrored: control.mirrored
        display: control.display
        alignment: control.display === IconLabel.IconOnly || control.display === IconLabel.TextUnderIcon ? Qt.AlignCenter : Qt.AlignLeft

        icon: control.icon
        text: control.text
        font: control.font
        color: Color.transparent(control.Universal.foreground, enabled ? 1.0 : 0.2)
    }

    background: Rectangle {
        implicitWidth: 100
        implicitHeight: 24

        visible: enabled && (control.down || control.highlighted || control.visualFocus || control.hovered)
        color: control.down ? control.Universal.listMediumColor :
               control.hovered ? control.Universal.listLowColor : control.Universal.altMediumLowColor

        Rectangle {
            width: parent.width
            height: parent.height
            visible: control.visualFocus || control.highlighted
            color: control.Universal.accent
            opacity: control.Universal.theme === Universal.Light ? 0.4 : 0.6
        }
    }
}
