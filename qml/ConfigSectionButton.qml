// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts

import Gremlin.Config
import Gremlin.Style
import "helpers.js" as Helpers

Button {
    id: _text

    required property int index
    required property string name
    required property ConfigGroupModel groupModel

    text: name

    height: 40
    width: _sectionSelector.width

    background: Row {
        Rectangle {
            width: 5
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            color: _sectionSelector.currentIndex == index ?
                Style.accent : Style.background
        }
        Rectangle {
            x: 5
            width: parent.width - 5
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            color: _sectionSelector.currentIndex == index ?
                Universal.chromeMediumColor : Style.background
        }
    }

    contentItem: JGText {
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
