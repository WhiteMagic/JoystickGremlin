// -*- coding: utf-8; -*-
// SPDX-License-Identifier: GPL-3.0-only

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Qt.labs.qmlmodels

import Gremlin.ActionPlugins
import Gremlin.Profile
import Kobold.Controls
import Kobold.Foundation


ColumnLayout {
    id: root

    required property MacroModel action

    readonly property int actionHeaderWidth: Metrics.controlHeight * 5
    readonly property int actionScrollbarWidth: Metrics.gapM * 2

    readonly property var actionTypes: [
        {value: "joystick", text: "Joystick"},
        {value: "key", text: "Keyboard"},
        {value: "logical-device", text: "Logical device"},
        {value: "mouse-button", text: "Mouse button"},
        {value: "mouse-motion", text: "Mouse motion"},
        {value: "pause", text: "Pause"},
        {value: "vjoy", text: "vJoy"}
    ]

    spacing: Metrics.gapM

    // +--------------------------------------------------------------------------------
    // | Repeat configuration
    // +--------------------------------------------------------------------------------
    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.gapM

        Label {
            text: "Repeat mode"
        }

        ComboBox {
            id: _repeatMode

            textRole: "text"
            valueRole: "value"

            model: [
                {value: "single", text: "Single"},
                {value: "count", text: "Count"},
                {value: "toggle", text: "Toggle"},
                {value: "hold", text: "Hold"}
            ]

            Component.onCompleted: {
                currentIndex = indexOfValue(root.action.repeatMode)
            }

            onActivated: { root.action.repeatMode = currentValue }
        }

        DoubleSpinBox {
            visible: ["count", "toggle", "hold"].includes(_repeatMode.currentValue)

            from: 0
            to: 3600
            stepSize: 0.1
            decimals: Metrics.defaultDecimalPlaces
            value: root.action.repeatDelay

            onValueModified: { root.action.repeatDelay = value }
        }

        SpinBox {
            visible: _repeatMode.currentValue === "count"

            editable: true
            from: 1
            to: 100
            value: root.action.repeatCount

            onValueModified: { root.action.repeatCount = value }
        }

        Spacer {}

        CheckBox {
            text: "Exclusive"
            checked: root.action.isExclusive

            onToggled: { root.action.isExclusive = checked }
        }
        CheckBox {
            visible: root.action.isExclusive
            text: "Pre-emptive"
            checked: root.action.isPreemptive

            onToggled: { root.action.isPreemptive = checked }
        }
    }

    // +--------------------------------------------------------------------------------
    // | Action step record and add controls.
    // +--------------------------------------------------------------------------------
    RowLayout {
        Layout.fillWidth: true
        spacing: Metrics.gapM

        Label {
            text: "Record inputs"
        }

        CheckBox {
            text: "Keyboard"
            checked: root.action.recordKeyboard
            enabled: !root.action.isRecording

            onToggled: { root.action.recordKeyboard = checked }
        }
        CheckBox {
            text: "Mouse"
            checked: root.action.recordMouse
            enabled: !root.action.isRecording

            onToggled: { root.action.recordMouse = checked }
        }
        CheckBox {
            text: "Axis"
            checked: root.action.recordJoystickAxis
            enabled: !root.action.isRecording

            onToggled: { root.action.recordJoystickAxis = checked }
        }
        CheckBox {
            text: "Button"
            checked: root.action.recordJoystickButton
            enabled: !root.action.isRecording

            onToggled: { root.action.recordJoystickButton = checked }
        }
        CheckBox {
            text: "Hat"
            checked: root.action.recordJoystickHat
            enabled: !root.action.isRecording

            onToggled: { root.action.recordJoystickHat = checked }
        }
        CheckBox {
            text: "Timings"
            checked: root.action.recordTimings
            enabled: !root.action.isRecording

            onToggled: { root.action.recordTimings = checked }
        }

        Button {
            visible: !root.action.isRecording
            text: "Start recording"

            onClicked: { root.action.startRecording() }
        }
        Button {
            visible: root.action.isRecording
            text: "Stop recording"

            onClicked: { root.action.stopRecording() }
        }

        Spacer {}

        AddActionMenuButton {
            variant: "bordered"
            text: "Add action"
            model: root.actionTypes.map((entry) => entry.text)

            onActionRequested: (name) => {
                root.action.addAction(
                    root.actionTypes.find((entry) => entry.text === name).value
                )
            }
        }
    }

    // Styled to appear as a backdrop for the list of actions.
    Rectangle {
        Layout.fillWidth: true
        Layout.preferredHeight: Math.min(_actionList.contentHeight, 400) + 2 * Metrics.gapS

        color: Theme.bgAlt
        radius: Metrics.radius * 2

        ScrollList {
            id: _actionList

            anchors.fill: parent
            anchors.margins: Metrics.gapS

            spacing: Metrics.gapS
            scrollbarAlwaysVisible: true
            reuseItems: true

            model: root.action.actions
            delegate: _delegateChooser

            Connections {
                target: _actionList.model

                function onActionAdded() {
                    // Reposition the view at the bottom of the list when an action is
                    // added but not when one is removed.
                    Qt.callLater(_actionList.positionViewAtEnd)
                }
            }
        }
    }

    // Renders the correct row content based on the step type.
    DelegateChooser {
        id: _delegateChooser

        role: "actionType"

        DelegateChoice {
            roleValue: "joystick"

            MacroActionRow {
                stepLabel: "Joystick"

                detailItem: RowLayout {
                    spacing: Metrics.gapM

                    InputCaptureButton {
                        Layout.fillWidth: true

                        eventTypes: ["axis", "button", "hat"]
                        multipleInputs: false
                        text: modelData.label ? modelData.label : "Record input"

                        callback: (inputs) => { modelData.updateJoystick(inputs) }
                    }

                    ButtonStateSelector {
                        visible: modelData.inputType === "button"

                        isPressed: modelData.isPressed
                        onStateModified: (isPressed) => { modelData.isPressed = isPressed }
                    }
                    AxisValueSpin {
                        visible: modelData.inputType === "axis"
                    }
                    HatDirectionCombo {
                        visible: modelData.inputType === "hat"
                    }
                }
            }
        }

        DelegateChoice {
            roleValue: "key"

            MacroActionRow {
                stepLabel: "Keyboard"

                detailItem: RowLayout {
                    spacing: Metrics.gapM

                    InputCaptureButton {
                        Layout.fillWidth: true

                        eventTypes: ["key"]
                        multipleInputs: false
                        text: modelData.key ? modelData.key : "Record input"

                        callback: (inputs) => { modelData.updateKey(inputs) }
                    }

                    ButtonStateSelector {
                        isPressed: modelData.isPressed
                        onStateModified: (isPressed) => { modelData.isPressed = isPressed }
                    }
                }
            }
        }

        DelegateChoice {
            roleValue: "logical-device"

            MacroActionRow {
                stepLabel: "Logical device"

                detailItem: RowLayout {
                    spacing: Metrics.gapM

                    LogicalDeviceSelector {
                        // The ordering is important, swapping it will result in the
                        // wrong item being displayed.
                        validTypes: ["axis", "button", "hat"]
                        logicalInputIdentifier: modelData.logicalInputIdentifier

                        onLogicalInputIdentifierChanged: {
                            modelData.logicalInputIdentifier = logicalInputIdentifier
                        }
                    }

                    Spacer {}

                    ButtonStateSelector {
                        visible: modelData.inputType === "button"

                        isPressed: modelData.isPressed
                        onStateModified: (isPressed) => { modelData.isPressed = isPressed }
                    }
                    RowLayout {
                        visible: modelData.inputType === "axis"
                        spacing: Metrics.gapM

                        AxisValueSpin {}
                        AxisModeRadios {}
                    }
                    HatDirectionCombo {
                        visible: modelData.inputType === "hat"
                    }
                }
            }
        }

        DelegateChoice {
            roleValue: "mouse-button"

            MacroActionRow {
                stepLabel: "Mouse button"

                detailItem: RowLayout {
                    spacing: Metrics.gapM

                    InputCaptureButton {
                        Layout.fillWidth: true

                        eventTypes: ["mouse"]
                        multipleInputs: false
                        text: modelData.button ? modelData.button : "Record input"

                        callback: (inputs) => { modelData.updateButton(inputs) }
                    }

                    ButtonStateSelector {
                        isPressed: modelData.isPressed
                        onStateModified: (isPressed) => { modelData.isPressed = isPressed }
                    }
                }
            }
        }

        DelegateChoice {
            roleValue: "mouse-motion"

            MacroActionRow {
                stepLabel: "Mouse motion"

                detailItem: RowLayout {
                    spacing: Metrics.gapM

                    Spacer {}

                    Label { text: "X axis" }
                    SpinBox {
                        editable: true
                        from: -10000
                        to: 10000
                        stepSize: 5
                        value: modelData.dx

                        onValueModified: { modelData.dx = value }
                    }

                    Label { text: "Y axis" }
                    SpinBox {
                        editable: true
                        from: -10000
                        to: 10000
                        stepSize: 5
                        value: modelData.dy

                        onValueModified: { modelData.dy = value }
                    }
                }
            }
        }

        DelegateChoice {
            roleValue: "pause"

            MacroActionRow {
                stepLabel: "Pause"

                detailItem: RowLayout {
                    spacing: Metrics.gapM

                    Spacer {}

                    DoubleSpinBox {
                        from: 0
                        to: 10
                        stepSize: 0.1
                        decimals: 2
                        value: modelData.duration

                        onValueModified: { modelData.duration = value }
                    }
                    Label { text: "seconds" }
                }
            }
        }

        DelegateChoice {
            roleValue: "vjoy"

            MacroActionRow {
                stepLabel: "vJoy"

                detailItem: RowLayout {
                    spacing: Metrics.gapM

                    VJoySelector {
                        validTypes: ["axis", "button", "hat"]

                        onSelectionChanged: (vjoyId, inputType, inputId) => {
                            modelData.vjoyId = vjoyId
                            modelData.inputType = inputType
                            modelData.inputId = inputId
                        }

                        Component.onCompleted: {
                            initialize(
                                modelData.vjoyId,
                                modelData.inputType,
                                modelData.inputId
                            )
                        }
                    }

                    Spacer {}

                    ButtonStateSelector {
                        visible: modelData.inputType === "button"

                        isPressed: modelData.isPressed
                        onStateModified: (isPressed) => { modelData.isPressed = isPressed }
                    }
                    RowLayout {
                        visible: modelData.inputType === "axis"
                        spacing: Metrics.gapM

                        AxisValueSpin {}
                        AxisModeRadios {}
                    }
                    HatDirectionCombo {
                        visible: modelData.inputType === "hat"
                    }
                }
            }
        }
    }

    // Local helpers -- factored out because the same `modelData.<field>` pattern
    // recurs across several step types (joystick/logical-device/vjoy all carry
    // axisValue and hatDirection; logical-device/vjoy both carry axisMode). Each
    // relies on the ambient `modelData` context property supplied by the
    // enclosing DelegateChoice, exactly as `MacroStepRow` below relies on the
    // ambient `index`/`modelData` supplied by the list view delegate.
    component AxisValueSpin: DoubleSpinBox {
        from: -1.0
        to: 1.0
        stepSize: 0.05
        decimals: 4
        value: modelData.axisValue

        onValueModified: { modelData.axisValue = value }
    }

    component AxisModeRadios: RowLayout {
        spacing: Metrics.gapM

        RadioButton {
            text: "Absolute"
            checked: modelData.axisMode === "absolute"

            onToggled: { modelData.axisMode = "absolute" }
        }
        RadioButton {
            text: "Relative"
            checked: modelData.axisMode === "relative"

            onToggled: { modelData.axisMode = "relative" }
        }
    }

    component HatDirectionCombo: ComboBox {
        textRole: "text"
        valueRole: "value"

        model: [
            {value: "center", text: "Center"},
            {value: "north", text: "North"},
            {value: "north-east", text: "North East"},
            {value: "east", text: "East"},
            {value: "south-east", text: "South East"},
            {value: "south", text: "South"},
            {value: "south-west", text: "South West"},
            {value: "west", text: "West"},
            {value: "north-west", text: "North West"}
        ]

        Component.onCompleted: {
            currentIndex = Qt.binding(() => indexOfValue(modelData.hatDirection))
        }

        onActivated: { modelData.hatDirection = currentValue }
    }

    // Renders the contents of a single action including control elements.
    component MacroActionRow: Item {
        id: _actionRow

        property string stepLabel: ""
        property alias detailItem: _detailLoader.sourceComponent
        // Gates Drag.active so the OS drag never starts before grabToImage()'s
        // async callback has set Drag.imageSource -- otherwise a fast flick can
        // cross the drag threshold before the ghost image exists.
        property bool _imageReady: false

        implicitWidth: _cells.implicitWidth
        implicitHeight: _cells.implicitHeight + 2 * Metrics.gapS
        // Reserve the scrollbar's gutter on the right so the row stays visually
        // disconnected from the track instead of butting up against it.
        width: ListView.view ? ListView.view.width - root.actionScrollbarWidth : implicitWidth
        height: implicitHeight

        Drag.active: _dragArea.drag.active && _actionRow._imageReady
        Drag.dragType: Drag.Automatic
        Drag.supportedActions: Qt.MoveAction
        Drag.proposedAction: Qt.MoveAction
        // Typed like the action/sequence drags: without a type key the bands below have
        // nothing to reject a foreign drag by, and its payload reaches parseInt regardless.
        Drag.mimeData: ({"text/plain": index.toString(), "type": "macro-step"})
        Drag.onDragFinished: (dropAction) => {
            if (dropAction === Qt.IgnoreAction) {
                signal.reloadCurrentInputItem()
            }
        }

        Rectangle {
            id: _background

            anchors.fill: parent
            radius: Metrics.radius
            color: Theme.bg
        }

        RowLayout {
            id: _cells

            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            implicitHeight: Metrics.rowAction
            spacing: Metrics.gapM

            Item {
                Layout.preferredWidth: Metrics.controlHeight
                Layout.preferredHeight: Metrics.controlHeight

                AppIcon {
                    anchors.centerIn: parent
                    name: "grip"
                    role: "fgMuted"
                }

                MouseArea {
                    id: _dragArea

                    anchors.fill: parent
                    cursorShape: Qt.OpenHandCursor
                    drag.target: _actionRow
                    drag.axis: Drag.YAxis

                    onPressed: {
                        _actionRow._imageReady = false
                        _actionRow.grabToImage((result) => {
                            _actionRow.Drag.imageSource = result.url
                            _actionRow._imageReady = true
                        })
                    }
                }
            }

            Label {
                Layout.preferredWidth: root.actionHeaderWidth
                text: _actionRow.stepLabel
            }

            Loader {
                id: _detailLoader

                Layout.fillWidth: true
            }

            ToolButton {
                icon.name: "delete"

                onClicked: { root.action.removeAction(index) }
            }
        }

        RowDropBand {
            id: _dropBandTop

            // While this row is itself being dragged, it physically follows the
            // cursor (drag.target above) -- its own band would otherwise trigger
            // on top of whatever row it happens to be passing over, showing a
            // second, unaligned insertion line alongside the real target row's.
            // Applies equally to _dropBandBottom below.
            enabled: !_dragArea.drag.active
            target: _background
            edge: "top"
            gap: Metrics.gapS
            // Steps are rows of this list, not actions -- an action or sequence drag would
            // otherwise parseInt its way into reordering an arbitrary step.
            validationCallback: (drop) => drop.getDataAsString("type") === "macro-step"
            dropCallback: (drop) => {
                const sourceIndex = parseInt(drop.text)
                if (index === 0) {
                    root.action.dropCallback(0, sourceIndex, "prepend")
                } else {
                    root.action.dropCallback(index - 1, sourceIndex, "append")
                }
            }
        }

        RowDropBand {
            id: _dropBandBottom

            enabled: !_dragArea.drag.active
            target: _background
            edge: "bottom"
            gap: Metrics.gapS
            validationCallback: (drop) => drop.getDataAsString("type") === "macro-step"
            dropCallback: (drop) => {
                const sourceIndex = parseInt(drop.text)
                root.action.dropCallback(index, sourceIndex, "append")
            }
        }
    }
}
