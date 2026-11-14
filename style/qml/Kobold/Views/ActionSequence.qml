// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQml.Models
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Composites
import Kobold.Foundation
import Kobold.Views

Item {
    id: _root

    property ActionSequenceModel sequence
    property InputItemModel inputItemModel
    property SequenceHeader headerWidget: _header

    implicitHeight: _content.height

    // Load on change or initial load.
    onSequenceChanged: () => { _actionTree._loadRootAction() }

    // An edit to the action tree rebuilds every ActionModel behind this
    // sequence, so the subtree has to be reloaded against the new models to
    // ensure edits are visible.
    Connections {
        target: _root.sequence

        function onRootActionChanged() {
            _actionTree._loadRootAction()
        }
    }

    Connections {
        target: signal

        function onReloadCurrentInputItem()
        {
            // Currently unused
        }
    }


    // Content
    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: Metrics.gapM
        // Extra right-hand room, so content clears the ListView's overlay
        // scrollbar.
        anchors.rightMargin: Metrics.gapM * 2
        spacing: Metrics.gapS

        // +--------------------------------------------------------------------
        // | Header
        // +--------------------------------------------------------------------
        SequenceHeader {
            id: _header

            Layout.fillWidth: true
            Layout.topMargin: -Metrics.actionRowInset

            sequence: _root.sequence
            inputItemModel: _root.inputItemModel
        }

        // +--------------------------------------------------------------------
        // | Render the root action node -- loaded through the same qmlPath
        // | mechanism every other action uses.
        // +--------------------------------------------------------------------
        ObjectLoader {
            id: _actionTree

            Layout.fillWidth: true
            // An empty sequence loads a real (0-height) RootAction, but
            // ColumnLayout still costs a spacing gap.
            visible: _root.sequence && _root.sequence.rootAction &&
                _root.sequence.rootAction.hasChildren

            // RootAction.qml declares `required property RootModel action`,
            // which only counts as initialized if supplied at creation time.
            function _loadRootAction() {
                if (_root.sequence && _root.sequence.rootAction) {
                    load(
                        Qt.createComponent(_root.sequence.rootAction.qmlPath),
                        { "action": _root.sequence.rootAction }
                    )
                }
            }
        }
    }
}