// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Templates as T
import Kobold.Foundation

T.ComboBox {
    id: control

    implicitHeight: Metrics.ctrlH
    implicitWidth: Math.max(Metrics.ctrlH * 5, leftPadding + contentItem.implicitWidth + rightPadding)
    leftPadding: Metrics.gapM
    rightPadding: Metrics.gapM + indicator.width + Metrics.gapS

    font.family: FontType.sans
    font.pixelSize: Metrics.textBody

    contentItem: Text {
        text: control.displayText
        color: control.enabled ? Theme.fg : Theme.fgDisabled
        font: control.font
        elide: Text.ElideRight
        verticalAlignment: Text.AlignVCenter
    }

    indicator: AppIcon {
        x: control.width - width - Metrics.gapM
        y: control.topPadding + (control.availableHeight - height) / 2
        name: "chevron-down"
        role: control.enabled ? "fg" : "fgDisabled"
    }

    background: Rectangle {
        radius: Metrics.radius
        color: Theme.bgAlt
        border.width: Metrics.hairline
        border.color: control.activeFocus || control.popup.visible ? Theme.accent : Theme.line
    }

    // Popup rule shared with Menu (SPEC/architecture: opaque fill, 1px line border,
    // zero shadow -- the classic place a shadow sneaks in).
    popup: T.Popup {
        y: control.height
        width: control.width
        implicitHeight: Math.min(contentItem.contentHeight, Metrics.ctrlH * 8)
        padding: 0

        contentItem: ListView {
            id: _popupList

            clip: true
            implicitHeight: contentHeight
            model: control.delegateModel
            currentIndex: control.highlightedIndex

            // Disable mobile-style kinetic/overshoot scrolling.
            flickableDirection: Flickable.VerticalFlick
            boundsBehavior: Flickable.StopAtBounds

            WheelHandler {
                onWheel: (event) => {
                    const topIndex = Math.max(0, _popupList.indexAt(0, _popupList.contentY + 1))
                    if (event.angleDelta.y > 0) {
                        _popupList.positionViewAtIndex(Math.max(0, topIndex - 3), ListView.Beginning)
                    } else {
                        _popupList.positionViewAtIndex(
                            Math.min(_popupList.count - 1, topIndex + 3),
                            ListView.Beginning
                        )
                    }
                    event.accepted = true
                }
            }
        }

        background: Rectangle {
            color: Theme.bgAlt
            border.width: Metrics.hairline
            border.color: Theme.line
        }
    }

    delegate: T.ItemDelegate {
        width: ListView.view.width
        height: Metrics.ctrlH
        highlighted: control.highlightedIndex === index

        contentItem: Text {
            leftPadding: Metrics.gapM
            // Not `Array.isArray(control.model)` -- a JS array literal assigned to the
            // (QVariant-typed) model property reads back as a QVariantList, which fails
            // that check even though `modelData` is populated correctly either way.
            // `model[control.textRole]` is only needed for genuine QAbstractItemModel
            // models (LogicalDeviceSelectorModel, ...), where there is no `modelData`.
            text: control.textRole
                ? (modelData !== undefined ? modelData[control.textRole] : model[control.textRole])
                : modelData
            color: Theme.fg
            font: control.font
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }

        background: Rectangle {
            color: parent.highlighted ? Theme.bgSelected : parent.hovered ? Theme.bgHover : "transparent"
        }
    }
}
