// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Layouts
import Kobold.Foundation

// SPEC §8: "Macro's steps are NOT child actions. Render as a table. If they look like
// nesting, the UI is lying." Generic table chrome only -- a header row of column labels and
// 1px-separated body rows, with row-edge-band drag reordering. Column content is whatever
// the caller supplies (a macro step's own fields are a plugin-body concern, Phase 7); this
// phase only establishes that steps are flat rows, never indented/guided ActionRows.
Item {
    id: root

    // columns: list<string> header labels.
    // rows: list<list<string>> one string per column, per row.
    property var columns: []
    property var rows: []

    signal moveRequested(int fromIndex, int toIndex)
    signal removeRequested(int index)

    implicitHeight: _table.implicitHeight
    implicitWidth: _table.implicitWidth

    ColumnLayout {
        id: _table

        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            spacing: Metrics.gapM

            Repeater {
                model: root.columns

                Text {
                    Layout.fillWidth: true
                    text: modelData
                    color: Theme.fgMuted
                    font.family: FontType.sans
                    font.pixelSize: Metrics.textDetail
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: Metrics.hairline
            color: Theme.line
        }

        // Each row is a single Item layout child; the drop-band and bottom rule are
        // overlaid on it via explicit positioning rather than added as further layout
        // children, or they would each claim their own extra row of height.
        Repeater {
            model: root.rows

            Item {
                id: _rowDelegate

                required property int index
                required property var modelData

                Layout.fillWidth: true
                implicitHeight: _cells.implicitHeight

                RowLayout {
                    id: _cells

                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    implicitHeight: Metrics.rowAction
                    spacing: Metrics.gapM

                    Repeater {
                        model: _rowDelegate.modelData

                        Text {
                            Layout.fillWidth: true
                            text: modelData
                            color: Theme.fg
                            font.family: FontType.sans
                            font.pixelSize: Metrics.textBody
                        }
                    }

                    Item {
                        Layout.preferredWidth: Metrics.ctrlH
                        Layout.preferredHeight: Metrics.ctrlH

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.OpenHandCursor
                        }
                    }
                }

                RowDropBand {
                    target: _cells
                    validationCallback: () => true
                    dropCallback: (drop) => root.moveRequested(parseInt(drop.text), _rowDelegate.index)
                }

                Rectangle {
                    visible: _rowDelegate.index < root.rows.length - 1
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: _cells.bottom
                    height: Metrics.hairline
                    color: Theme.line
                }
            }
        }
    }
}
