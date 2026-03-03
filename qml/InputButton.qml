// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls

import Gremlin.Style

Button {
    id: _control

    property bool selected: false
    property Component deleteButton: null
    property Component editButton: null

    background: Rectangle {
        border.color: hovered ? Style.accent : selected ? Style.accent : Style.backgroundShade
        border.width: 1
        color: selected ? Universal.chromeMediumColor : Style.background
    }

    contentItem: Item {
        JGText {
            id: _inputLabel
            text: name
            font.weight: 600

            width: Math.min(implicitWidth, parent.width - 30)
            elide: Text.ElideRight

            anchors.top: parent.top
            anchors.left: parent.left
        }

        Loader {
            sourceComponent: _control.editButton

            anchors.top: parent.top
            anchors.left: _inputLabel.right
        }

        Loader {
            active: actionSequenceDisplayMode === "Count"

            anchors.bottom: parent.bottom
            anchors.right: parent.right

            sourceComponent: Label {
                text: actionSequenceCount

                horizontalAlignment: Text.AlignRight
                verticalAlignment: Text.AlignVCenter
            }
        }

        Loader {
            visible: actionSequenceDisplayMode === "Full"

            anchors.bottom: parent.bottom
            anchors.right: parent.right

            sourceComponent: Image {
                source: "image://action_summary/" + actionSequenceDescriptor
                asynchronous: false
                cache: false
                width: sourceSize.width
                height: sourceSize.height

            }
        }

        JGText {
            id: _inputDescription
            text: description
            font.italic: true

            width: parent.width
            elide: Text.ElideRight

            anchors.left: parent.left
            anchors.bottom: parent.bottom
        }

        Loader {
            sourceComponent: _control.deleteButton

            anchors.top: parent.top
            anchors.right: parent.right
        }
    }
}
