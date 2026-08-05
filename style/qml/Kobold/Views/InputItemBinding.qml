// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtQml.Models

import Gremlin.ActionPlugins
import Gremlin.Profile

import Kobold.Foundation
import Kobold.Composites
import Kobold.Views


// SPEC §8: sequences are independent trees, separated by space -- never a rule between them
// (that's the ListView's job in qml/InputConfiguration.qml). Vertical separation from
// neighboring trees is entirely the ghost "New Action Sequence" row's gapS margin now
// (InputConfiguration.qml) -- this item reserves none of its own, or the two would stack.
Item {
    id: _root

    property InputItemBindingModel inputBinding
    property InputItemModel inputItemModel
    property BindingHeader headerWidget: _header

    implicitHeight: _content.height

    // Reruns the Loader's one-shot setSource whenever inputBinding itself changes (not
    // just on first creation) -- otherwise a delegate recycled for a different row
    // (ListView reuseItems) keeps showing the previous row's action tree, since `visible`
    // alone doesn't reliably toggle across the swap (e.g. both rows have children).
    onInputBindingChanged: _actionTree._loadRootAction()

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
        // Extra right-hand room, so content clears the ListView's overlay scrollbar (SPEC
        // ScrollBar.qml, Metrics.gapM wide) instead of sitting flush under it -- the gap the
        // left pane's input list gets for free by narrowing its own delegate width
        // (DeviceInputList.qml). Content padding only; the delegate's own width
        // (qml/InputConfiguration.qml) stays untouched.
        anchors.rightMargin: Metrics.gapM * 2
        // No top margin -- vertical separation from the previous tree is the ghost row's
        // gapS margin above (InputConfiguration.qml), not this item's own padding.
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

        // Axis/hat "virtual button" activation UI (SPEC doesn't cover this row -- it isn't
        // part of the binding-header grammar, hence its own component).
        ActivationBehavior {
            Layout.fillWidth: true

            inputBinding: _root.inputBinding
        }

        // +--------------------------------------------------------------------
        // | Render the root action node -- loaded through the same qmlPath mechanism
        // | every other action uses, rather than a hardcoded static type.
        // +--------------------------------------------------------------------
        Loader {
            id: _actionTree

            Layout.fillWidth: true
            // An empty sequence loads a real (0-height) RootAction, but ColumnLayout still
            // costs a spacing gap around a merely-0-height row -- hasChildren collapses the
            // row itself, same as ActivationBehavior does for its own inapplicable case.
            visible: _root.inputBinding && _root.inputBinding.rootAction &&
                _root.inputBinding.rootAction.hasChildren

            // setSource()'s initial-properties argument, not source: + onLoaded --
            // RootAction.qml's root declares `required property RootModel action`,
            // which only counts as initialized if supplied at creation time. Called both
            // on creation and from _root.onInputBindingChanged above.
            function _loadRootAction() {
                if (_root.inputBinding && _root.inputBinding.rootAction) {
                    setSource(
                        _root.inputBinding.rootAction.qmlPath,
                        { "action": _root.inputBinding.rootAction }
                    )
                }
            }

            Component.onCompleted: _loadRootAction()
        }
    }
}