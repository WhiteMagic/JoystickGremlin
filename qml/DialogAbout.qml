// -*- coding: utf-8; -*-
//
// Copyright (C) 2015 - 2019 Lionel Ott
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.


import QtQuick 2.13
import QtQuick.Controls 2.13
import QtQuick.Layouts 1.13
import QtQuick.Window 2.13
import QtWebView 1.13

import QtQuick.Controls.Universal 2.12


Window {
    minimumWidth: 640
    minimumHeight: 480
    color: Universal.background
    title: qsTr("About")

    ColumnLayout {
        anchors.fill: parent

        TabBar {
            id: bar

            TabButton {
                text: qsTr("About")
            }
            TabButton {
                text: qsTr("License")
            }
            TabButton {
                text: qsTr("3rd Party Licenses")
            }
        }

        StackLayout {
            currentIndex: bar.currentIndex

            WebView {
                id: aboutTab
                url: "../about/about.html"
            }
            WebView {
                id: licenseTab
                url: "../about/joystick_gremlin.html"
            }
            WebView {
                id: thirdpartyTab

                url: "../about/third_party_licenses.html"
            }
        }
    }
}