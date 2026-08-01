// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

import QtQuick.Controls.Universal
import QtQuick.Shapes
import Qt.labs.qmlmodels

import QtCharts

import Gremlin.ActionPlugins
import Gremlin.Base
import Gremlin.Profile
import Gremlin.Style
import "../../qml"

import "render_helpers.js" as RH


Item {
    id: _root

    property ResponseCurveModel action
    property Deadzone deadzone: action.deadzone
    property alias widgetSize : _vis.size
    readonly property int handleOffset: 5

    // Present the numerical values on a 0 to 100 range rather than the
    // [-1, 1] range the curve is stored in. Purely a display option, the
    // curve data is unaffected.
    property bool percentScale: false

    // Amount a single click of a numerical input moves its value by. Slopes
    // read the same in either scale, so their step is a fixed one.
    readonly property real coordinateStep: percentScale ? 0.1 : 0.05
    readonly property real slopeStep: 0.01

    implicitHeight: _content.height

    focus: true
    Keys.onDeletePressed: () => {
        action.removeControlPoint(action.selectedPoint)
    }

    // The numerical inputs latch their range and precision when they are
    // created, so changing the display scale rebuilds them.
    onPercentScaleChanged: () => {
        _pointPanel.active = false
        _pointPanel.active = true
        _deadzonePanel.active = false
        _deadzonePanel.active = true
    }

    function toDisplay(value) {
        return percentScale ? RH.to_percent(value) : value
    }

    function fromDisplay(value) {
        return percentScale ? RH.from_percent(value) : value
    }

    function lengthToDisplay(value) {
        return percentScale ? RH.length_to_percent(value) : value
    }

    function lengthFromDisplay(value) {
        return percentScale ? RH.length_from_percent(value) : value
    }

    function formatDisplay(value) {
        return toDisplay(value).toFixed(percentScale ? 2 : 3)
    }

    function map2u(x) {
        return RH.x2u(x, _curve.x, _vis.size, handleOffset)
    }

    function map2v(y) {
        return RH.y2v(y, _curve.x, _vis.size, handleOffset)
    }

    function map2x(u, du) {
        return RH.u2x(
            du === null ? u : u + du - handleOffset,
            handleOffset,
            _vis.size
        )
    }
    function map2y(v, dv) {
        return RH.v2y(
            dv === null ? v : v + dv - handleOffset,
            handleOffset,
            _vis.size
        )
    }

    function updateControlPoint(cp_handle, evt, index) {
        let new_x = RH.clamp(map2x(cp_handle.x, evt.x), -1.0, 1.0)
        let new_y = RH.clamp(map2y(cp_handle.y, evt.y ), -1.0, 1.0)

        // Ensure the points at either end cannot be moved away from the edge
        if (index === 0) {
            new_x = -1.0
        }
        if (index === action.controlPoints.length - 1) {
            new_x = 1.0
        }

        // In symmetry mode moving the center point, if there is one is
        // not allowed
        if (_root.action.isSymmetric && _repeater.count % 2 !== 0 &&
            index * 2 + 1 === _repeater.count)
        {
            return null
        }

        // Prevent moving control point past neighoring ones
        let new_u = RH.clamp(map2u(new_x), -handleOffset, _vis.size + handleOffset)
        let new_v = RH.clamp(map2v(new_y), -handleOffset, _vis.size + handleOffset)

        let left = _repeater.itemAt(index - 1)
        let right = _repeater.itemAt(index + 1)
        if (left && left.item.x > new_u) {
            new_u = cp_handle.x
            new_x = map2x(cp_handle.x, null)
        }
        if (right && right.item.x < new_u) {
            new_u = cp_handle.x
            new_x = map2x(cp_handle.x, null)
        }

        // Move the actual marker
        cp_handle.x = new_u
        cp_handle.y = new_v

        // Handle symmetry mode, no need to update model as
        // the code does this behind the scenes with the
        // model update below
        if (_root.action.isSymmetric) {
            let mirror = _repeater.itemAt(_repeater.count - index - 1).item
            mirror.x = map2u(-new_x, null)
            mirror.y = map2v(-new_y, null)

        }

        // Return the computed new [x, y] coordinates in [-1, 1] to use on the
        // model side of things
        return [new_x, new_y]
    }

    ColumnLayout {
        id: _content

        anchors.left: parent.left
        anchors.right: parent.right

        // Various controls to configure curve editing
        RowLayout {
            Layout.fillWidth: true

            ComboBox {
                Layout.preferredWidth: 200

                model: ["Piecewise Linear", "Cubic Spline", "Cubic Bezier Spline"]

                Component.onCompleted: () => {
                    currentIndex = find(_root.action.curveType)
                }
                onActivated: () => { _root.action.curveType = currentText }
            }

            Button {
                text: "Invert Curve"

                onClicked: () => { _root.action.invertCurve() }
            }

            CheckBox {
                text: "Symmetric"

                checked: _root.action.isSymmetric

                onToggled: () => { _root.action.isSymmetric = checked }
            }

            CheckBox {
                text: "0 - 100 scale"

                checked: _root.percentScale

                onToggled: () => { _root.percentScale = checked }

                ToolTip {
                    text: "Shows the numerical values on a 0 to 100 range " +
                        "instead of -1 to 1, which is how pedal travel is " +
                        "usually expressed. Slopes are the same in either " +
                        "scale and the curve itself is not modified."

                    width: Style.tooltipMaxWidth
                    visible: parent.hovered
                    delay: Style.tooltipDelayMs
                }
            }
        }

        // Response curve widget
        RowLayout {
            Layout.preferredWidth: 475

            Item {
                id: _vis

                property int size: 450
                property int border: 2

                Component.onCompleted: () => { action.setWidgetSize(size) }

                width: size + 2 * border
                height: size + 2 * border

                // Display the background image.
                Image {
                    width: _vis.size
                    height: _vis.size
                    x: _vis.border
                    y: _vis.border
                    source: Style.isDarkMode ? "grid_dark.svg" : "grid.svg"

                    Rectangle {
                        anchors.fill: parent
                        color: "transparent"
                        border.color: Style.foreground
                        border.width: 1
                    }
                }

                // Render the response curve itself without interactive elements.
                Shape {
                    id: _curve

                    width: _vis.size
                    height: _vis.size

                    anchors.centerIn: parent

                    preferredRendererType: Shape.CurveRenderer

                    ShapePath {
                        strokeColor: "#808080"

                        strokeWidth: 2
                        fillColor: "transparent"

                        PathPolyline {
                            path: action.linePoints
                        }
                    }

                    MouseArea {
                        anchors.fill: parent

                        hoverEnabled: true

                        onDoubleClicked: (evt) => {
                            action.addControlPoint(
                                2 * (evt.x / width) - 1,
                                -2 * (evt.y / height) + 1
                            )
                        }
                        onPositionChanged: (evt) => { _probe.sample(evt.x) }
                        onExited: () => { _probe.active = false }
                    }
                }

                // Read-out of the curve's value and slope under the cursor.
                Item {
                    id: _probe

                    property bool active: false
                    property real curveX: 0.0
                    property real curveY: 0.0
                    property real slope: 0.0

                    // Position of the curve point in widget coordinates.
                    readonly property real markerU: (curveX + 1) / 2 * _vis.size
                    readonly property real markerV: _vis.size - (curveY + 1) / 2 * _vis.size

                    function sample(mouseX) {
                        curveX = RH.clamp(2 * (mouseX / _vis.size) - 1, -1.0, 1.0)
                        let info = action.curveInfoAt(curveX)
                        curveY = info[0]
                        slope = info[1]
                        active = true
                    }

                    x: _curve.x
                    y: _curve.y
                    width: _vis.size
                    height: _vis.size

                    visible: active

                    // Vertical guide at the sampled input value.
                    Rectangle {
                        x: _probe.markerU
                        width: 1
                        height: _vis.size
                        color: Style.accent
                        opacity: 0.5
                    }

                    // Horizontal guide at the resulting output value.
                    Rectangle {
                        y: _probe.markerV
                        width: _vis.size
                        height: 1
                        color: Style.accent
                        opacity: 0.5
                    }

                    Rectangle {
                        x: _probe.markerU - 3
                        y: _probe.markerV - 3
                        width: 6
                        height: 6
                        radius: 3
                        color: Style.accent
                    }

                    // Numerical read-out, kept inside the widget so it stays
                    // legible near the edges of the curve.
                    Rectangle {
                        x: RH.clamp(_probe.markerU + 10, 0, _vis.size - width)
                        y: RH.clamp(_probe.markerV - height - 10, 0, _vis.size - height)

                        width: _probeText.width + 10
                        height: _probeText.height + 6

                        color: Style.background
                        border.color: Style.medColor
                        border.width: 1
                        opacity: 0.9

                        Label {
                            id: _probeText

                            anchors.centerIn: parent

                            text: "x " + _root.formatDisplay(_probe.curveX) +
                                "   y " + _root.formatDisplay(_probe.curveY) +
                                "   slope " + _probe.slope.toFixed(2)
                        }
                    }
                }

                // Render the individual control elements.
                Repeater {
                    id: _repeater

                    model: action.controlPoints

                    delegate: Component {
                        // Pick the correct control visualization to load and pass
                        // the repeater reference in.
                        Loader {
                            Component.onCompleted: () => {
                                let url = modelData.hasHandles ? "HandleControl.qml" : "PointControl.qml"
                                setSource(
                                    url,
                                    {
                                        "repeater": _repeater,
                                        "focusTarget": _root
                                    }
                                )
                            }
                        }
                    }
                }
            }

            Loader {
                id: _pointPanel

                Layout.alignment: Qt.AlignTop

                sourceComponent: _pointPanelComponent
            }
        }

        Label {
            text: "Deadzone"
        }

        Loader {
            id: _deadzonePanel

            sourceComponent: _deadzonePanelComponent
        }
    }

    // Numerical editing of the selected control point.
    Component {
        id: _pointPanelComponent

        ColumnLayout {
            GridLayout {
                columns: 2

                Label {
                    Layout.preferredWidth: 30

                    text: "X"
                }

                FloatSpinBox {
                    id: _coordX

                    minValue: _root.toDisplay(-1.0)
                    maxValue: _root.toDisplay(1.0)
                    stepSize: _root.coordinateStep
                    decimals: _root.percentScale ?
                        Style.decimalsStandard : Style.decimalsPrecise
                    value: _root.toDisplay(_root.action.selectedPointCoord.x)

                    onValueModified: (newValue) => {
                        _root.action.updateSelectedPoint(
                            _root.fromDisplay(newValue),
                            _root.fromDisplay(_coordY.value)
                        )
                    }
                }

                Label {
                    text: "Y"
                }

                FloatSpinBox {
                    id: _coordY

                    minValue: _root.toDisplay(-1.0)
                    maxValue: _root.toDisplay(1.0)
                    stepSize: _root.coordinateStep
                    decimals: _root.percentScale ?
                        Style.decimalsStandard : Style.decimalsPrecise
                    value: _root.toDisplay(_root.action.selectedPointCoord.y)

                    onValueModified: (newValue) => {
                        _root.action.updateSelectedPoint(
                            _root.fromDisplay(_coordX.value),
                            _root.fromDisplay(newValue)
                        )
                    }
                }
            }

            // Numerical editing of the selected point's control handles,
            // which only the Bezier spline possesses. Slopes are scale
            // independent, only the handle lengths are converted.
            ColumnLayout {
                visible: _root.action.hasControlHandles

                CheckBox {
                    text: "Mirror handles"

                    checked: _root.action.selectedSymmetricHandles
                    enabled: _root.action.selectedHasLeftHandle &&
                        _root.action.selectedHasRightHandle

                    onToggled: () => {
                        _root.action.selectedSymmetricHandles = checked
                    }

                    ToolTip {
                        text: "Keeps both handles of the selected point " +
                            "mirrored, so the curve leaves it with the " +
                            "same slope on either side."

                        width: Style.tooltipMaxWidth
                        visible: parent.hovered
                        delay: Style.tooltipDelayMs
                    }
                }

                GridLayout {
                    columns: 2

                    Label {
                        Layout.columnSpan: 2

                        text: "Left handle"
                        visible: _root.action.selectedHasLeftHandle
                    }

                    Label {
                        Layout.preferredWidth: 45

                        text: "Slope"
                        visible: _root.action.selectedHasLeftHandle
                    }

                    FloatSpinBox {
                        id: _leftSlope

                        minValue: -10.0
                        maxValue: 10.0
                        stepSize: _root.slopeStep
                        decimals: Style.decimalsPrecise
                        visible: _root.action.selectedHasLeftHandle
                        value: _root.action.selectedLeftSlope

                        onValueModified: (newValue) => {
                            _root.action.selectedLeftSlope = newValue
                        }
                    }

                    Label {
                        text: "Length"
                        visible: _root.action.selectedHasLeftHandle
                    }

                    FloatSpinBox {
                        id: _leftLength

                        minValue: 0.0
                        maxValue: _root.lengthToDisplay(2.0)
                        stepSize: _root.coordinateStep
                        decimals: _root.percentScale ?
                            Style.decimalsStandard : Style.decimalsPrecise
                        visible: _root.action.selectedHasLeftHandle
                        value: _root.lengthToDisplay(
                            _root.action.selectedLeftLength)

                        onValueModified: (newValue) => {
                            _root.action.selectedLeftLength =
                                _root.lengthFromDisplay(newValue)
                        }
                    }

                    Label {
                        Layout.columnSpan: 2

                        text: "Right handle"
                        visible: _root.action.selectedHasRightHandle
                    }

                    Label {
                        text: "Slope"
                        visible: _root.action.selectedHasRightHandle
                    }

                    FloatSpinBox {
                        id: _rightSlope

                        minValue: -10.0
                        maxValue: 10.0
                        stepSize: _root.slopeStep
                        decimals: Style.decimalsPrecise
                        visible: _root.action.selectedHasRightHandle
                        value: _root.action.selectedRightSlope

                        onValueModified: (newValue) => {
                            _root.action.selectedRightSlope = newValue
                        }
                    }

                    Label {
                        text: "Length"
                        visible: _root.action.selectedHasRightHandle
                    }

                    FloatSpinBox {
                        id: _rightLength

                        minValue: 0.0
                        maxValue: _root.lengthToDisplay(2.0)
                        stepSize: _root.coordinateStep
                        decimals: _root.percentScale ?
                            Style.decimalsStandard : Style.decimalsPrecise
                        visible: _root.action.selectedHasRightHandle
                        value: _root.lengthToDisplay(
                            _root.action.selectedRightLength)

                        onValueModified: (newValue) => {
                            _root.action.selectedRightLength =
                                _root.lengthFromDisplay(newValue)
                        }
                    }
                }
            }

            Connections {
                target: _root.action

                function onSelectedPointChanged() {
                    _coordX.value =
                        _root.toDisplay(_root.action.selectedPointCoord.x)
                    _coordY.value =
                        _root.toDisplay(_root.action.selectedPointCoord.y)
                    _leftSlope.value = _root.action.selectedLeftSlope
                    _leftLength.value =
                        _root.lengthToDisplay(_root.action.selectedLeftLength)
                    _rightSlope.value = _root.action.selectedRightSlope
                    _rightLength.value =
                        _root.lengthToDisplay(_root.action.selectedRightLength)
                }
            }
        }
    }

    Component {
        id: _deadzonePanelComponent

        RowLayout {
            // Lower half axis.
            NumericalRangeSlider {
                id: _lowerDeadzone

                from: _root.toDisplay(-1.0)
                to: _root.toDisplay(0.0)
                firstValue: _root.toDisplay(_root.deadzone.low)
                secondValue: _root.toDisplay(_root.deadzone.centerLow)
                stepSize: _root.coordinateStep
                decimals: _root.percentScale ? Style.decimalsStandard : 3

                onFirstValueChanged: () => {
                    _root.deadzone.low = _root.fromDisplay(firstValue)
                }
                onSecondValueChanged: () => {
                    _root.deadzone.centerLow = _root.fromDisplay(secondValue)
                }
            }

            // Upper half axis.
            NumericalRangeSlider {
                id: _upperDeadzone

                from: _root.toDisplay(0.0)
                to: _root.toDisplay(1.0)
                firstValue: _root.toDisplay(_root.deadzone.centerHigh)
                secondValue: _root.toDisplay(_root.deadzone.high)
                stepSize: _root.coordinateStep
                decimals: _root.percentScale ? Style.decimalsStandard : 3

                onFirstValueChanged: () => {
                    _root.deadzone.centerHigh = _root.fromDisplay(firstValue)
                }
                onSecondValueChanged: () => {
                    _root.deadzone.high = _root.fromDisplay(secondValue)
                }
            }
        }
    }
}
