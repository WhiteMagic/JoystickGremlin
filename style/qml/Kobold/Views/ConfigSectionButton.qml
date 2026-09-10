// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Config
import Kobold.Foundation
import "helpers.js" as Helpers

Button {
    id: _text

    required property int index
    required property string name
    required property ConfigGroupModel groupModel

    text: name

    height: Metrics.rowInput
    width: _sectionSelector.width

    background: Rectangle {
        color: _sectionSelector.currentIndex == index ? Theme.bgSelected : Theme.bg
        border.width: Metrics.hairline
        border.color: Theme.line
        radius: Metrics.radius

        // Two-channel selection, matching InputButton: fill + accent left bar.
        Rectangle {
            visible: _sectionSelector.currentIndex == index
            width: Metrics.accentMark
            color: Theme.accent
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: parent.left
        }
    }

    contentItem: Label {
        text: Helpers.capitalize(_text.text)
        font: _text.font
        horizontalAlignment: Text.AlignLeft
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }

    onClicked: function () {
        _sectionSelector.currentIndex = index
        _configSection.groupModel = groupModel
    }
}
