// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only
//
// The Kobold style playground (guide §6 Phase 3): a permanent gallery
// showing every implemented control across state/theme/zoom. This is not
// throwaway -- it stays in the repo as the reference and visual-check
// surface for every later phase. Run via `poetry run python
// scripts/gallery.py`.
//
// Frozen state swatches use directly-settable properties only (checked,
// enabled, down). hovered/visualFocus are engine-managed and read-only, so
// hover/focus are demonstrated live on a plain instance instead -- move the
// mouse over it or Tab to it (matches guide §7's "hover-any-row" manual
// check rather than faking a frozen hover snapshot).

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import Kobold.Foundation

Window {
    id: root

    width: Metrics.windowWidth
    height: Metrics.windowHeight
    visible: true
    color: Theme.bg
    title: "Kobold Playground"

    Shortcut { sequence: "L"; onActivated: themeManager.set_theme("light") }
    Shortcut { sequence: "D"; onActivated: themeManager.set_theme("dark") }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // -- Toolbar: theme + zoom toggles ---------------------------------
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: Metrics.toolbar
            color: Theme.bgAlt
            border.width: Metrics.hairline
            border.color: Theme.line

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: Metrics.gapL
                anchors.rightMargin: Metrics.gapL
                spacing: Metrics.gapM

                Text {
                    text: "Kobold Playground"
                    color: Theme.fg
                    font.family: FontType.sans
                    font.pixelSize: Metrics.textBody
                    font.weight: FontType.semiBold
                }

                Item { Layout.fillWidth: true }

                Caption { text: "Theme:" }
                Button {
                    text: "Light"
                    onClicked: themeManager.set_theme("light")
                }
                Button {
                    text: "Dark"
                    onClicked: themeManager.set_theme("dark")
                }

                Caption { text: "Zoom:" }
                Button {
                    text: "100%"
                    onClicked: themeManager.set_ui_scale("100")
                }
                Button {
                    text: "150%"
                    onClicked: themeManager.set_ui_scale("150")
                }
                Button {
                    text: "200%"
                    onClicked: themeManager.set_ui_scale("200")
                }
            }
        }

        // -- Public / Internal tab switch --------------------------------
        TabBar {
            id: _galleryTabs

            Layout.fillWidth: true
            currentIndex: 0

            TabButton { text: "Public" }
            TabButton { text: "Internal" }
        }

        // -- Gallery body -----------------------------------------------------
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: _galleryTabs.currentIndex

            PublicGallery {}
            InternalGallery {}
        }
    }
}
