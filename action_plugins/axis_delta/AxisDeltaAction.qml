// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Universal
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.ActionPlugins
import Gremlin.Profile
import Gremlin.Style
import "../../qml"

Item {
    id: _root

    property AxisDeltaModel action

    implicitHeight: _content.height

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        // +-------------------------------------------------------------------
        // | Threshold configuration
        // +-------------------------------------------------------------------
        RowLayout {
            Label {
                text: "Change threshold"
            }
            FloatSpinBox {
                minValue: 0.0001
                maxValue: 2.0
                stepSize: 0.05
                value: _root.action.changeThreshold

                onValueModified: (newValue) => {
                    _root.action.changeThreshold = newValue
                }
            }
            LayoutHorizontalSpacer {}
        }

        // +-------------------------------------------------------------------
        // | Positive change actions
        // +-------------------------------------------------------------------
        RowLayout {
            Label {
                text: "Positive change"
            }

            Rectangle {
                Layout.fillWidth: true
            }

            ActionSelector {
                actionNode: _root.action
                callback: function(x) { _root.action.appendAction(x, "positive"); }
            }
        }

        Rectangle {
            id: _positiveDivider
            Layout.fillWidth: true
            height: 2
            color: Style.lowColor
        }

        Repeater {
            model: _root.action.getActions("positive")

            delegate: ActionNode {
                action: modelData
                parentAction: _root.action
                containerName: "positive"

                Layout.fillWidth: true
            }
        }

        // +-------------------------------------------------------------------
        // | Negative change actions
        // +-------------------------------------------------------------------
        RowLayout {
            Label {
                text: "Negative change"
            }

            Rectangle {
                Layout.fillWidth: true
            }

            ActionSelector {
                actionNode: _root.action
                callback: function(x) { _root.action.appendAction(x, "negative"); }
            }
        }

        Rectangle {
            id: _negativeDivider
            Layout.fillWidth: true
            height: 2
            color: Style.lowColor
        }

        Repeater {
            model: _root.action.getActions("negative")

            delegate: ActionNode {
                action: modelData
                parentAction: _root.action
                containerName: "negative"

                Layout.fillWidth: true
            }
        }
    }

    ActionDragDropArea {
        target: _positiveDivider
        dropCallback: function(drop) {
            modelData.dropAction(drop.text, modelData.sequenceIndex, "positive");
        }
    }

    ActionDragDropArea {
        target: _negativeDivider
        dropCallback: function(drop) {
            modelData.dropAction(drop.text, modelData.sequenceIndex, "negative");
        }
    }
}
