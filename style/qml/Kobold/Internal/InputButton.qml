// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import Kobold.Foundation

// SPEC §9 input row. Row 1: identifier (never elided away entirely by
// layout collapse -- fixed 48px height) + description (intent). Row 2:
// chips (structure) or a plain count, gated by the "action-sequence-
// information" Option. An unbound row (no description, no chips) is still
// a complete 48px row, not a truncated one.
Button {
    id: _control

    property bool selected: false
    property Component editButton: null
    property Component deleteButton: null

    // Data contract. Declared explicitly as `required` (rather than relied
    // on as ambient delegate-injected context properties) so a real
    // QAbstractListModel's matching-named roles bind here directly -- a
    // plain, non-required property of the same name would just keep its
    // default and never receive the model's role value -- and plain
    // test/gallery data works identically via literal assignment.
    required property string name
    required property string description
    required property int actionSequenceCount
    required property string actionSequenceDisplayMode
    required property var actionLabels

    // Declaring any required property switches Qt's delegate binding to
    // strict mode, which disables the legacy `index`/`model` context
    // properties entirely -- so `index` must be requested explicitly too.
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

    // Refresh when this row's underlying action data changed elsewhere
    // (e.g. edited in the right pane).
    Connections {
        target: signal
        function onInputItemChanged(itemIndex) {
            if (itemIndex === index) {
                _delayedUpdate.start()
            }
        }
    }

    Component.onCompleted: () => { _updateShownChipCount() }

    Timer {
        id: _delayedUpdate
        interval: 50
        repeat: false
        onTriggered: _updateShownChipCount()
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

    // Greedy fit: lay out chips left to right, reserving room for an
    // overflow chip unless every remaining label already fits. Never
    // pre-truncate by a fixed count -- measure, then drop.
    function _computeShownChipCount(labels, availableWidth) {
        if (labels.length === 0) {
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
        if (actionSequenceDisplayMode !== "Chips") {
            return
        }
        _shownChipCount = _computeShownChipCount(actionLabels, _chipArea.width)
    }

    background: Rectangle {
        color: _control.selected ? Theme.bgSelected : Theme.bg
        border.width: Metrics.hairline
        border.color: Theme.line
        radius: Metrics.radius

        // Two-channel selection (SPEC §9): fill + accent left bar, together.
        Rectangle {
            visible: _control.selected
            width: Metrics.accentMark
            color: Theme.accent
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.left: parent.left
        }
    }

    // Edit/delete sit outside contentItem's padded area, flush against the
    // card's own right edge -- not inset by _control's content padding.
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
        // Flush against the card edge only when there's actually a button
        // there; otherwise sit at the normal padded content edge, same as
        // when there's no button at all -- description's right anchor
        // (below) follows this either way.
        anchors.rightMargin: _control.deleteButton ? Metrics.hairline : Metrics.gapM
        z: 1
    }

    contentItem: Item {
        id: _content

        // -- Row 1: identifier + description. --
        Text {
            id: _identifier
            text: name
            color: Theme.fg
            font.family: FontType.sans
            font.weight: FontType.semiBold
            font.pixelSize: Metrics.textBody

            width: Math.min(implicitWidth, parent.width - 30)
            elide: Text.ElideRight

            anchors.top: parent.top
            anchors.left: parent.left
        }

        Text {
            id: _description
            text: description
            visible: text !== ""
            color: Theme.fgMuted
            font.family: FontType.sans
            font.weight: FontType.regular
            font.pixelSize: Metrics.textDetail

            elide: Text.ElideRight
            horizontalAlignment: Text.AlignRight

            anchors.top: parent.top
            anchors.left: _identifier.right
            anchors.leftMargin: Metrics.gapM
            // _editButtonLoader is reparented onto _control (see below), so
            // it isn't a sibling here -- anchors can't reach it. Map its
            // left edge into this item's coordinate space instead.
            width: Math.max(0,
                _editButtonLoader.mapToItem(_content, 0, 0).x - x - Metrics.gapM)
        }

        // -- Row 2: chips (structure) or a plain count, per Options setting. --
        Item {
            id: _chipArea
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: Metrics.textDetail + Metrics.gapS

            // This Item's own width (not _control's) is what the fit
            // calculation needs -- Control's content-item resize can settle
            // after _control.onWidthChanged has already fired once.
            onWidthChanged: _updateShownChipCount()

            Row {
                visible: actionSequenceDisplayMode === "Chips"
                spacing: Metrics.gapS
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter

                Repeater {
                    model: actionLabels

                    // `index` here is this Repeater's own index, shadowing
                    // the outer ListView delegate's `index` used above --
                    // scoped to this delegate only.
                    delegate: Chip {
                        text: modelData
                        visible: index < _control._shownChipCount
                    }
                }

                Chip {
                    overflow: true
                    visible: actionSequenceDisplayMode === "Chips"
                        && _control._shownChipCount < actionLabels.length
                    text: "+" + (actionLabels.length - _control._shownChipCount)
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
