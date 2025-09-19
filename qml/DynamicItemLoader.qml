// -*- coding: utf-8; -*-
//
// Copyright (C) 2025
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
//
// ---------------------------------------------------------------------------
// DynamicItemLoader
// ---------------------------------------------------------------------------
// Reusable helper component to load another QML file at runtime (expects a
// fully-formed qrc:/ or other valid QML source URL already normalized by the
// caller), integrate it into layouts, and keep sizing (implicitHeight) in
// sync. Designed to replace ad‑hoc Qt.createComponent usage with a concise
// declarative Loader wrapper.
//
// Features:
//  * Accepts absolute (Windows/Unix) or relative paths, qrc:, file:/// URLs.
//  * Optional automatic reload when the path changes.
//  * Exposes the loaded item via the 'dynamicItem' alias.
//  * Injects an 'action' object (common pattern in this project) and any
//    additional key/value pairs via 'injectedProperties'.
//  * Provides a reload() method to force reloading (e.g. after file overwrite).
//  * Robust implicitHeight propagation with fallback to height.
//  * Emits signals on successful load or error.
// ---------------------------------------------------------------------------

import QtQuick
import QtQuick.Layouts

Item {
    id: root

    // Fully-formed QML source URL (e.g. qrc:/... ). Caller guarantees validity.
    property string qmlPath: ""

    // Optional object passed to a loaded component with an 'action' property.
    property var action: null

    // Arbitrary properties to set on the created item (after onLoaded).
    // Example: { someProp: 42, model: myModel }
    property var injectedProperties: ({})

    // Legacy 'expanded' / 'active' flags removed; component always attempts
    // to load when qmlPath is set.

    // Automatically reload when qmlPath changes.
    property bool autoReloadOnPathChange: true

    // Expose the created object for external bindings.
    property alias dynamicItem: _loader.item


    // If true, the loader will be forced to recreate the item when qmlPath
    // changes even if the new path string is identical (useful after file
    // overwrites); implemented by briefly toggling active off and on.
    property bool forceReloadOnIdenticalPath: false

    // Height follows loaded content; fallback to height if implicitHeight unset.
    implicitHeight: dynamicItem ? (dynamicItem.implicitHeight > 0
                                   ? dynamicItem.implicitHeight
                                   : dynamicItem.height) : 0

    // Let layouts stretch us horizontally by default.
    Layout.fillWidth: true
    // Always visible; caller can hide externally if needed.
    visible: true

    signal loaded(Item item)
    signal loadError(string source, string errorString)

    function reload() {
        // Force refresh by toggling active when a path exists
        if (_loader.active) {
            _loader.active = false;
            _loader.active = !!root.qmlPath;
        } else {
            _loader.active = !!root.qmlPath;
        }
    }

    onQmlPathChanged: if (autoReloadOnPathChange) {
        if (forceReloadOnIdenticalPath)
            reload();
        else
            _loader.active = !!root.qmlPath;
    }

    // Core Loader doing the work.
    Loader {
        id: _loader
        // Note: 'active' is controlled externally when properties change.
    active: !!root.qmlPath
        asynchronous: true
    source: root.qmlPath
        anchors.left: parent.left
        anchors.right: parent.right

        onStatusChanged: {
            if (status === Loader.Error) {
                console.log("DynamicItemLoader: error loading", source, errorString());
                root.loadError(source, errorString());
            }
        }
        onLoaded: {
            if (item) {
                // Inject standard action property if present.
                if (root.action && item.hasOwnProperty("action")) {
                    item.action = root.action;
                }
                // Apply any additional injected properties.
                if (root.injectedProperties && typeof root.injectedProperties === 'object') {
                    for (let k in root.injectedProperties) {
                        try { item[k] = root.injectedProperties[k]; } catch(e) { /* ignore assignment errors */ }
                    }
                }
                // If inside a Layout, ensure it expands horizontally when possible.
                if (item.Layout) {
                    item.Layout.fillWidth = true;
                }
                root.loaded(item);
            }
        }
    }

}
