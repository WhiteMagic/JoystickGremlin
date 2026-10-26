// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick

// Provides the same functionality as the Loader component, but without some
// of the memory issues arising from it in how Gremlin uses it.
Item {
    id: _root

    // Resize the item to the parent's size.
    property bool resizeItem: true
    property Item item: null

    implicitWidth: item ? item.implicitWidth : 0
    implicitHeight: item ? item.implicitHeight : 0

    // Callers create the component, so urls and lookups resolve at the call
    // site.
    function load(component, properties) {
        _unload()
        let created = component.createObject(_root, properties)
        if (created === null) {
            console.error(component.errorString())
            return
        }
        if (resizeItem) {
            created.width = Qt.binding(() => _root.width)
        }
        item = created
    }

    function _unload() {
        // If the item exists it will be destroyed in a deferred manner, thus
        // hiding it prevents visual bugs.
        if (item) {
            item.visible = false
            item.destroy()
            item = null
        }
    }
}
