// -*- coding: utf-8; -*-
//
// Copyright (C) 2025 Lionel Ott
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

    // Internal flag driving Loader.active to avoid rebinding warnings. We
    // mutate this property instead of imperatively assigning Loader.active,
    // keeping the Loader's 'active' binding stable.
    property bool _activeFlag: false

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
        // Toggle the flag to force re-instantiation. Use callLater so the
        // event loop processes deactivation before reactivation.
        if (!_activeFlag) {
            _activeFlag = !!root.qmlPath;
            return;
        }
        _activeFlag = false;
        Qt.callLater(function(){
            _activeFlag = !!root.qmlPath;
        });
    }

    onQmlPathChanged: if (autoReloadOnPathChange) {
        if (forceReloadOnIdenticalPath)
            reload();
        else
            _activeFlag = !!root.qmlPath;
    }

    Component.onCompleted: _activeFlag = !!root.qmlPath;

    // Core Loader doing the work.
    Loader {
        id: _loader
        // Note: 'active' is controlled externally when properties change.
        active: root._activeFlag
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
