import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import Gremlin.ActionPlugins
import Gremlin.Util

import "../../qml"


Item {
    property var comparator : null

    implicitWidth: _content.implicitWidth
    implicitHeight: _content.implicitHeight

    RowLayout {
        id: _content

        Loader {
            active: comparator && comparator.typeName === "pressed"

            Layout.preferredWidth: active ? implicitWidth : 0

            sourceComponent: RowLayout {
                ComboBox {
                    model: ["Pressed", "Released"]
                    onActivated: () => {
                        comparator.isPressed = currentValue
                    }
                    Component.onCompleted: () => {
                        currentIndex = active ? indexOfValue(comparator.isPressed) : 0
                    }
                }
            }
        }

        Loader {
            active: comparator && comparator.typeName === "range"

            Layout.preferredWidth: active ? implicitWidth : 0

            sourceComponent: RowLayout {
                Label { text: "between" }

                FloatSpinBox {
                    id: _lower

                    minValue: -1.0
                    maxValue: _upper.value
                    stepSize: 0.05
                    value: active ? comparator.lowerLimit : 0.0

                    onValueModified: (newValue) => {
                        comparator.lowerLimit = newValue
                    }
                }

                Label { text: "and" }

                FloatSpinBox {
                    id: _upper

                    minValue: _lower.value
                    maxValue: 1.0
                    stepSize: 0.05
                    value: active ? comparator.upperLimit : 0.0

                    onValueModified: (newValue) => {
                        comparator.upperLimit = newValue
                    }
                }
            }
        }

        Loader {
            active: comparator && comparator.typeName === "direction"

            Layout.preferredWidth: active ? implicitWidth : 0

            sourceComponent: RowLayout {
                HatDirectionSelectorV2 {
                    directions: active ? comparator.model : null
                }
            }
        }
    }
}