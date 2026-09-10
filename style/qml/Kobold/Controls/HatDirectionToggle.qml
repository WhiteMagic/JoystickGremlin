// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Kobold.Foundation

// Used to select hat directions from a single row of arrows indicating the eight
// directions of a hat. The selection and hover state of the directions is visually
// indicated.
RowLayout {
    id: root

    spacing: Metrics.gapS

    property bool north: false
    property bool northEast: false
    property bool east: false
    property bool southEast: false
    property bool south: false
    property bool southWest: false
    property bool west: false
    property bool northWest: false

    signal northEdited(bool value)
    signal northEastEdited(bool value)
    signal eastEdited(bool value)
    signal southEastEdited(bool value)
    signal southEdited(bool value)
    signal southWestEdited(bool value)
    signal westEdited(bool value)
    signal northWestEdited(bool value)

    ToolButton {
        id: _north
        checkable: true
        checked: root.north
        icon.name: "arrow-n"
        iconRole: checked ? "accent" : "fg"
        background: ToggleBackground { control: _north }
        onToggled: { root.northEdited(checked) }
    }
    ToolButton {
        id: _northEast
        checkable: true
        checked: root.northEast
        icon.name: "arrow-ne"
        iconRole: checked ? "accent" : "fg"
        background: ToggleBackground { control: _northEast }
        onToggled: { root.northEastEdited(checked) }
    }
    ToolButton {
        id: _east
        checkable: true
        checked: root.east
        icon.name: "arrow-e"
        iconRole: checked ? "accent" : "fg"
        background: ToggleBackground { control: _east }
        onToggled: { root.eastEdited(checked) }
    }
    ToolButton {
        id: _southEast
        checkable: true
        checked: root.southEast
        icon.name: "arrow-se"
        iconRole: checked ? "accent" : "fg"
        background: ToggleBackground { control: _southEast }
        onToggled: { root.southEastEdited(checked) }
    }
    ToolButton {
        id: _south
        checkable: true
        checked: root.south
        icon.name: "arrow-s"
        iconRole: checked ? "accent" : "fg"
        background: ToggleBackground { control: _south }
        onToggled: { root.southEdited(checked) }
    }
    ToolButton {
        id: _southWest
        checkable: true
        checked: root.southWest
        icon.name: "arrow-sw"
        iconRole: checked ? "accent" : "fg"
        background: ToggleBackground { control: _southWest }
        onToggled: { root.southWestEdited(checked) }
    }
    ToolButton {
        id: _west
        checkable: true
        checked: root.west
        icon.name: "arrow-w"
        iconRole: checked ? "accent" : "fg"
        background: ToggleBackground { control: _west }
        onToggled: { root.westEdited(checked) }
    }
    ToolButton {
        id: _northWest
        checkable: true
        checked: root.northWest
        icon.name: "arrow-nw"
        iconRole: checked ? "accent" : "fg"
        background: ToggleBackground { control: _northWest }
        onToggled: { root.northWestEdited(checked) }
    }

    // Renders a background under a ToolButton to show hover and selection state.
    component ToggleBackground: Rectangle {
        property var control

        radius: Metrics.radius
        color: !control.enabled ? "transparent"
             : control.down ? Theme.bgSelected
             : control.hovered ? Theme.bgHover
             : "transparent"

        Rectangle {
            visible: control.checked
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            height: Metrics.accentMark
            color: Theme.accent
        }

        Rectangle {
            visible: control.visualFocus
            anchors.fill: parent
            anchors.margins: -2
            radius: parent.radius
            color: "transparent"
            border.width: 2
            border.color: Theme.accent
        }
    }

}
