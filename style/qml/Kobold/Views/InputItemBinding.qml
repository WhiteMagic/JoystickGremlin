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

    property InputItemBindingModel inputBinding
    property InputItemModel inputItemModel
    property BindingHeader headerWidget: _header

    implicitHeight: _content.height

    // Load on change or initial load.
    onInputBindingChanged: _actionTree._loadRootAction()

    // An edit to the action tree rebuilds every ActionModel behind this
    // sequence, so the subtree has to be reloaded against the new models to
    // ensure edits are visible.
    Connections {
        target: _root.inputBinding

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
        BindingHeader {
            id: _header

            Layout.fillWidth: true
            Layout.topMargin: -Metrics.actionRowInset

            inputBinding: _root.inputBinding
            inputItemModel: _root.inputItemModel
        }

        // Axis/hat "virtual button" activation UI (SPEC doesn't cover this
        // row -- it isn't part of the binding-header grammar, hence its own
        // component).
        ActivationBehavior {
            Layout.fillWidth: true

            inputBinding: _root.inputBinding
        }

        // +--------------------------------------------------------------------
        // | Render the root action node -- loaded through the same qmlPath
        // | mechanism| every other action uses.
        // +--------------------------------------------------------------------
        ObjectLoader {
            id: _actionTree

            Layout.fillWidth: true
            // An empty sequence loads a real (0-height) RootAction, but
            // ColumnLayout still costs a spacing gap.
            visible: _root.inputBinding && _root.inputBinding.rootAction &&
                _root.inputBinding.rootAction.hasChildren

            // RootAction.qml declares `required property RootModel action`,
            // which only counts as initialized if supplied at creation time.
            function _loadRootAction() {
                if (_root.inputBinding && _root.inputBinding.rootAction) {
                    load(
                        Qt.createComponent(_root.inputBinding.rootAction.qmlPath),
                        { "action": _root.inputBinding.rootAction }
                    )
                }
            }
        }
    }
}