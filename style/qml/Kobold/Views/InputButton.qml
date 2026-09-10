// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls

import Kobold.Controls
import Kobold.Foundation

// Shows a single input button of a device. Contains two rows:
// Row 1: Identifier and action description (if present)
// Row 2: Action chips and/or number of actions
Button {
    id: _control

    property bool selected: false
    property Component editButton: null
    property Component deleteButton: null

    // Properties visualized on the row.
    required property string name
    required property string description
    required property int actionSequenceCount
    required property string actionSequenceDisplayMode
    required property var actionLabels

    required property int index

    implicitHeight: Metrics.rowInput
    leftPadding: Metrics.gapM
    rightPadding: Metrics.gapM
    topPadding: Metrics.gapS
    bottomPadding: Metrics.gapS

    property int _shownChipCount: 0

    Connections {
        target: _control
        function onWidthChanged() { _updateShownChipCount() }
    }

    // Update the widget's content when the input it represents has its configuration
    // changed.
    Connections {
        target: signal

        function onInputItemChanged(itemIndex) {
            if (itemIndex === index) {
                _delayedUpdate.start()
            }
        }
    }

    Component.onCompleted: () => { _updateShownChipCount() }
    onActionSequenceDisplayModeChanged: () => { _updateShownChipCount() }

    Timer {
        id: _delayedUpdate

        interval: 50
        repeat: false
        onTriggered: () => { _updateShownChipCount() }
    }

    TextMetrics {
        id: _measureChipText

        font.family: FontType.sans
        font.pixelSize: Metrics.textDetail
        font.weight: FontType.regular
    }

    function _chipWidth(text) {
        _measureChipText.text = text
        return _measureChipText.width + Metrics.gapM
    }

    // Computes the number of chips to shown, starting at the first until the available
    // space is exhausted. Reserves space for an overlfow indicator chip.
    function _computeShownChipCount(labels, availableWidth) {
        if (!labels || labels.length === 0) {
            return 0
        }

        let total = 0
        let shown = 0
        for (let i = 0; i < labels.length; i++) {
            const width = _chipWidth(labels[i])
            const isLast = i === labels.length - 1
            const overflowWidth = isLast
                ? 0
                : Metrics.gapS + _chipWidth("+" + (labels.length - i - 1))
            const candidateTotal = total + (shown > 0 ? Metrics.gapS : 0) + width
            if (candidateTotal + overflowWidth > availableWidth) {
                break
            }
            total = candidateTotal
            shown++
        }
        return shown
    }

    function _updateShownChipCount() {
        if (actionSequenceDisplayMode !== "Chips" || !actionLabels) {
            return
        }
        _shownChipCount = _computeShownChipCount(actionLabels, _chipArea.width)
    }

    // Background of the button, flat color with a accent bar on the left.
    background: Rectangle {
        color: _control.selected ? Theme.bgSelected : Theme.bg
        border.width: Metrics.hairline
        border.color: Theme.line
        radius: Metrics.radius

        Rectangle {
            visible: _control.selected
            width: Metrics.accentMark
            color: Theme.accent
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: parent.left
        }
    }

    // Buttons available only for logical inputs to edit their label or delete them.
    Loader {
        id: _editButtonLoader

        parent: _control
        sourceComponent: _control.editButton
        anchors.top: _control.top
        anchors.topMargin: Metrics.gapS
        anchors.right: _deleteButtonLoader.left
        z: 1
    }

    Loader {
        id: _deleteButtonLoader

        parent: _control
        sourceComponent: _control.deleteButton
        anchors.top: _control.top
        anchors.topMargin: Metrics.gapS
        anchors.right: _control.right
        anchors.rightMargin: _control.deleteButton ? Metrics.hairline : Metrics.gapM
        z: 1
    }

    // Content shown on top of the button's background.
    contentItem: Item {
        id: _content

        // Row 1: identifier + description.
        Label {
            id: _identifier

            text: name

            width: Math.min(implicitWidth, parent.width - 30)
            elide: Text.ElideRight

            anchors.top: parent.top
            anchors.left: parent.left
        }

        Label {
            id: _description

            text: description
            visible: text !== ""
            color: Theme.fgMuted
            font.pixelSize: Metrics.textDetail

            elide: Text.ElideRight
            horizontalAlignment: Text.AlignRight

            anchors.top: parent.top
            anchors.left: _identifier.right
            anchors.leftMargin: Metrics.gapM
            width: Math.max(0,
                _editButtonLoader.mapToItem(_content, 0, 0).x - x - Metrics.gapM)
        }

        // Row 2: Action chips or a action count.
        Item {
            id: _chipArea
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.bottomMargin: Metrics.gapS
            height: Metrics.textDetail + Metrics.gapS

            onWidthChanged: _updateShownChipCount()

            Row {
                visible: actionSequenceDisplayMode === "Chips"
                spacing: Metrics.gapS
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter

                Repeater {
                    model: actionLabels

                    delegate: Chip {
                        text: modelData
                        visible: index < _control._shownChipCount
                    }
                }

                Chip {
                    overflow: true
                    visible: actionSequenceDisplayMode === "Chips"
                        && _control._shownChipCount < (actionLabels ? actionLabels.length : 0)
                    text: "+" + ((actionLabels ? actionLabels.length : 0) - _control._shownChipCount)
                }
            }

            Label {
                visible: actionSequenceDisplayMode === "Count"
                text: actionSequenceCount
                font.pixelSize: Metrics.textDetail
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
}
