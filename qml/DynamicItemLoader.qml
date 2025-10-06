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
    id: _dynamicRoot

    // Fully-formed QML source URL (e.g. qrc:/... ).
    property string qmlPath: ""

    // Optional object passed to a loaded component with an 'action' property.
    property var action: null

    // Arbitrary properties to set on the created item (after onLoaded).
    // Example: { someProp: 42, model: myModel }
    property var injectedProperties: ({})

    // Automatically reload when qmlPath changes.
    property bool autoReloadOnPathChange: true

    // Expose the created object for external bindings.
    property alias dynamicItem: _loader.item

    // If true, the loader will be forced to recreate the item when qmlPath
    // changes even if the new path string is identical.
    property bool forceReloadOnIdenticalPath: false

    // Internal flag driving Loader.active to avoid rebinding warnings. We
    // mutate this property instead of imperatively assigning Loader.active,
    // keeping the Loader's 'active' binding stable.
    property bool _activeFlag: false

    // Height tracks that of the dynamically loaded content. Fallback handling
    // if the 'implicitHeight' is not set.
    implicitHeight: dynamicItem ? (dynamicItem.implicitHeight > 0
                                ? dynamicItem.implicitHeight
                                : dynamicItem.height) : 0

    // Signals communicating load status.
    signal loaded(Item item)
    signal loadError(string source, string errorString)

    function reload() {
        // Toggle the flag to force re-instantiation. Use callLater so the
        // event loop processes deactivation before reactivation.
        if (!_activeFlag) {
            _activeFlag = !!_dynamicRoot.qmlPath
            return
        }
        _activeFlag = false
        Qt.callLater(function() {
            _activeFlag = !!_dynamicRoot.qmlPath
        })
    }

    onQmlPathChanged: () => {
        if (autoReloadOnPathChange) {
            if (forceReloadOnIdenticalPath) {
                reload()
            }
            else {
                _activeFlag = !!_dynamicRoot.qmlPath
            }
        }
    }

    Component.onCompleted: () => {
        _activeFlag = !!_dynamicRoot.qmlPath
    }

    // Core Loader performing all the actual loading.
    Loader {
        id: _loader

        anchors.left: parent.left
        anchors.right: parent.right

        // Note: 'active' is controlled externally when properties change.
        active: _dynamicRoot._activeFlag
        asynchronous: true
        source: _dynamicRoot.qmlPath

        onStatusChanged: (src, errStr) => {
            if (status === Loader.Error) {
                console.log("DynamicItemLoader: error loading", src, errStr())
                _dynamicRoot.loadError(src, errStr())
            }
        }
        onLoaded: (item) => {
            if (item) {
                // Inject standard action property if present.
                if (_dynamicRoot.action && item.hasOwnProperty("action")) {
                    item.action = _dynamicRoot.action
                }
                // Apply any additional injected properties.
                if (_dynamicRoot.injectedProperties &&
                    typeof root.injectedProperties === 'object')
                {
                    for (let k in _dynamicRoot.injectedProperties) {
                        try {
                            item[k] = _dynamicRoot.injectedProperties[k]
                        }
                        catch(e) { /* ignore assignment errors */ }
                    }
                }
                _dynamicRoot.loaded(item)
            }
        }
    }

}