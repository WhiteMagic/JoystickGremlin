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

    height: Metrics.rowCompact
    width: _sectionSelector.width

    background: Row {
        Rectangle {
            width: Metrics.accentMark
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            color: _sectionSelector.currentIndex == index ?
                Theme.accent : Theme.bg
        }
        Rectangle {
            x: Metrics.accentMark
            width: parent.width - Metrics.accentMark
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            color: _sectionSelector.currentIndex == index ?
                Theme.bgSelected : Theme.bg
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
