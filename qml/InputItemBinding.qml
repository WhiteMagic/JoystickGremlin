// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import QtQml.Models

import QtQuick.Controls.Universal

import Gremlin.ActionPlugins
import Gremlin.Profile

import Kobold.Foundation
import Kobold.Internal


// SPEC §8: sequences are independent trees, separated by space + each sequence's own
// padding -- never a rule between them (that's the ListView's job in
// qml/InputConfiguration.qml). This item's own 8px padding is that "each sequence's 8px
// padding".
Item {
    id: _root

    property InputItemBindingModel inputBinding
    property InputItemModel inputItemModel
    property BindingHeader headerWidget: _header

    implicitHeight: _content.height + Metrics.gapM * 2

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
        anchors.margins: Metrics.gapM
        // Extra right-hand room on top of the uniform margin above, so content clears the
        // ListView's overlay scrollbar (SPEC ScrollBar.qml, Metrics.gapM wide) instead of
        // sitting flush under it -- the gap the left pane's input list gets for free by
        // narrowing its own delegate width (DeviceInputList.qml). Content padding only; the
        // delegate's own width (qml/InputConfiguration.qml) stays untouched.
        anchors.rightMargin: Metrics.gapM * 2
        spacing: Metrics.gapS

        // +--------------------------------------------------------------------
        // | Header
        // +--------------------------------------------------------------------
        BindingHeader {
            id: _header

            Layout.fillWidth: true

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

            // setSource()'s initial-properties argument, not source: + onLoaded --
            // RootAction.qml's root declares `required property RootModel action`,
            // which only counts as initialized if supplied at creation time.
            Component.onCompleted: setSource(
                _root.inputBinding.rootAction.qmlPath,
                { "action": _root.inputBinding.rootAction }
            )
        }
    }
}