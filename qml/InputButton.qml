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

    property int _descriptionWidth: 0
    property int _actionWidth: 0
    property bool _actionTruncated: false

    Connections {
        target: _control

        function onWidthChanged() {
            updateWidths()
        }
    }

    Connections {
        target: signal

        function onInputItemChanged(itemIndex) {
            if (itemIndex === index) {
                delayedUpdate.start()
            }
        }
    }

    Component.onCompleted: () => { updateWidths() }

    Timer {
        id: delayedUpdate
        interval: 50
        repeat: false
        onTriggered: updateWidths()
    }

    function updateWidths() {
        let imageWidth = _actionSequenceFull ? _actionSequenceFull.item.sourceSize.width : 0
        let widths = computeWidths(imageWidth, _inputDescription.text)

        _actionTruncated = widths[1] < imageWidth
        _descriptionWidth = widths[0]
        _actionWidth = widths[1]
    }

    function computeWidths(imageWidth, text) {
        let descriptionWidth = 0
        let actionWidth = 0

        let countWidth = 15
        let spacing = 30
        let textPadding = 10

        // If the description is empty, we can use the entire width for the
        // action information.
        if (text.length == 0) {
            actionWidth = Math.min(_control.width, imageWidth)
        }

        // Otherwise, if the action display style is just the count we reserve
        // space for the number and give the rest to the label.
        else if (actionSequenceDisplayMode === "Count") {
            descriptionWidth = _control.width - countWidth - spacing
            actionWidth = countWidth
        }

        // Finally, if we display an image representing the action, we have to
        // figure out if everything can fit together, or if both have to be
        // truncated.
        else {
            _textMetrics.text = text
            let textWidth = _textMetrics.width + textPadding

            let actionLimit = _control.width * 0.3
            let textLimit = _control.width * 0.7 - spacing

            if (imageWidth < actionLimit) {
                actionWidth = imageWidth
                descriptionWidth = Math.min(textWidth, _control.width - actionWidth - spacing)
            }
            else if (textWidth < textLimit) {
                descriptionWidth = textWidth + spacing
                actionWidth = Math.min(imageWidth, _control.width - descriptionWidth)
            }
            else {
                actionWidth = actionLimit
                descriptionWidth = textLimit
            }
        }

        return [descriptionWidth, actionWidth]
    }

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

                width: _actionWidth

                horizontalAlignment: Text.AlignRight
                verticalAlignment: Text.AlignVCenter
            }
        }

        Loader {
            id: _actionSequenceFull

            visible: actionSequenceDisplayMode === "Full"

            anchors.bottom: parent.bottom
            anchors.right: parent.right

            sourceComponent: Image {
                source: "image://action_summary/" + actionSequenceDescriptor
                asynchronous: false
                cache: false
                clip: true

                width: _actionWidth
                height: sourceSize.height

                fillMode: Image.Pad
                horizontalAlignment: Image.AlignLeft
            }
        }

        JGText {
            id: _inputDescription
            text: description
            font.italic: true

            width: _descriptionWidth
            elide: Text.ElideRight

            anchors.left: parent.left
            anchors.bottom: parent.bottom
        }

        TextMetrics {
            id: _textMetrics
            font: _inputDescription.font
        }

        Loader {
            sourceComponent: _control.deleteButton

            anchors.top: parent.top
            anchors.right: parent.right
        }
    }

    HoverHandler {
        id: _hover
    }

    ToolTip {
        visible: _hover.hovered && actionSequenceDisplayMode === "Full" && _actionTruncated
        delay: 400

        x: _hover.point.position.x + 16
        y: _hover.point.position.y + 16

        contentItem: Image {
            source: _actionSequenceFull.item ? _actionSequenceFull.item.source : ""
            fillMode: Image.PreserveAspectFit
            width: implicitWidth
            height: implicitHeight
        }
    }

}
