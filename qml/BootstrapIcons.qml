import QtQuick




Item {
    property alias icons: _icon_names
    // property alias loaded: loader.loaded
    property alias resource: _loader.resource

    readonly property string family: "bootstrap-icons"

    FontLoader {
        id: _loader

        property string resource

        source: resource
    }

    BootstrapIconsNames {
        id: _icon_names
    }
}