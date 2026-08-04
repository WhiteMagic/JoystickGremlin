// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import Gremlin.Config
import Kobold.Controls
import "helpers.js" as Helpers

ScrollColumn {
    property ConfigGroupModel groupModel

    scrollbarAlwaysVisible: true

    Repeater {
        model: groupModel
        delegate: ConfigGroup {}
    }
}
