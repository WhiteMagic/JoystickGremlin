// main.qml
//
// Pure-QML drag & drop reorderable list with animated drop gaps.
//
// Trigger model: the LEADING EDGE of the dragged card is the drag hot spot
// (bottom edge when moving down, top edge when moving up). The gap opens
// when that edge enters the top 25% / bottom 25% band of a neighbouring
// row, computed from DragEvent.y inside one full-height DropArea per row.
// Only the band facing the direction of travel is live.
//
// Run standalone:   qml main.qml        (Qt 6.5+)
//
// Pattern source: Qt "QML Dynamic View Ordering Tutorial", chapters 2 & 3
//   https://doc.qt.io/qt-6/qml-dynamicview-tutorial.html
// Gap animation:  ListView::displaced (see "ViewTransition" docs)

import QtQuick
import QtQuick.Controls.Basic
import QtQml.Models

ApplicationWindow {
    id: window

    width: 400
    height: 600
    visible: true
    title: qsTr("Reorderable List")

    // ---- tweakables ---------------------------------------------------
    readonly property int  gapDuration: 220         // how fast the gap opens
    readonly property int  rowHeight: 68
    readonly property int  rowInset: 6              // visual spacing, kept INSIDE the delegate
    readonly property real zoneFraction: 0.25       // top/bottom trigger band height
    // Reversal hysteresis: how far the cursor must travel AGAINST the current
    // direction before the leading edge flips. A flip relocates the hot spot
    // by a whole row height and (per the Drag docs) immediately re-emits a
    // drag move, so a spurious flip costs a visible one-row jump. Keep this
    // comfortably above hand jitter.
    readonly property real directionThreshold: rowHeight * 0.2

    header: ToolBar {
        Label {
            anchors.centerIn: parent
            text: qsTr("Press and hold a row, then drag to reorder")
            font.pixelSize: 13
        }
    }

    // ---- source model -------------------------------------------------
    ListModel {
        id: fruitModel

        ListElement { name: "Apple";      detail: "Malus domestica";      accent: "#e74c3c" }
        ListElement { name: "Banana";     detail: "Musa acuminata";       accent: "#f1c40f" }
        ListElement { name: "Cherry";     detail: "Prunus avium";         accent: "#c0392b" }
        ListElement { name: "Date";       detail: "Phoenix dactylifera";  accent: "#8e6f47" }
        ListElement { name: "Elderberry"; detail: "Sambucus nigra";       accent: "#5b2c6f" }
        ListElement { name: "Fig";        detail: "Ficus carica";         accent: "#7d6608" }
        ListElement { name: "Grape";      detail: "Vitis vinifera";       accent: "#6c3483" }
        ListElement { name: "Kiwi";       detail: "Actinidia deliciosa";  accent: "#7d9b28" }
        ListElement { name: "Lemon";      detail: "Citrus limon";         accent: "#d4ac0d" }
        ListElement { name: "Mango";      detail: "Mangifera indica";     accent: "#e67e22" }
    }

    // ---- visual model: reorders WITHOUT modifying fruitModel ------------
    DelegateModel {
        id: visualModel

        model: fruitModel
        delegate: dragDelegate
    }

    Component {
        id: dragDelegate

        // The delegate root is a MouseArea acting purely as a container:
        // a view positions its delegate root itself, so the root can never
        // be moved by drag. The child "content" item is what we drag.
        MouseArea {
            id: dragArea

            required property string name
            required property string detail
            required property string accent

            // Current position in the VISUAL order (not the source model order).
            readonly property int visualIndex: DelegateModel.itemsIndex

            property bool held: false

            // -1 = moving up, +1 = moving down, 0 = not yet established.
            property int dragDirection: 0
            property real trackedY: 0

            anchors {
                left: parent?.left
                right: parent?.right
            }
            height: window.rowHeight

            // Only bind the drag target after press-and-hold, so a plain
            // drag still flicks the ListView instead of grabbing a row.
            drag.target: held ? content : undefined
            drag.axis: Drag.YAxis
            pressAndHoldInterval: 250           // 800 ms default feels sluggish on desktop

            onPressAndHold: {
                dragArea.dragDirection = 0
                dragArea.trackedY = content.mapToItem(null, 0, 0).y
                dragArea.held = true
            }
            onReleased: {
                dragArea.held = false
                dragArea.dragDirection = 0
            }
            onCanceled: {
                dragArea.held = false
                dragArea.dragDirection = 0
            }

            // Direction tracking with hysteresis. trackedY follows the
            // furthest extent of the current run; reversing requires
            // directionThreshold px of travel against it, so a wiggle at
            // standstill can't flip the leading edge.
            //
            // Sampled in SCENE coordinates, not content.y: ParentChange
            // preserves visual position on pick-up, so scene y is continuous
            // across the reparent. content.y is not -- it rebases from
            // delegate-local to window-local and would read as a jump.
            function trackDirection(newY) {
                const delta = newY - dragArea.trackedY

                if (dragArea.dragDirection > 0) {
                    if (delta > 0)
                        dragArea.trackedY = newY                    // extend the downward run
                    else if (-delta > window.directionThreshold)
                        dragArea.setDirection(-1, newY)
                } else if (dragArea.dragDirection < 0) {
                    if (delta < 0)
                        dragArea.trackedY = newY                    // extend the upward run
                    else if (delta > window.directionThreshold)
                        dragArea.setDirection(1, newY)
                } else if (Math.abs(delta) > window.directionThreshold) {
                    // The FIRST direction needs the threshold too, otherwise a
                    // 1 px twitch on pick-up decides which edge leads.
                    dragArea.setDirection(delta > 0 ? 1 : -1, newY)
                }
            }

            function setDirection(dir, y) {
                dragArea.dragDirection = dir
                dragArea.trackedY = y
            }

            // Which band of this row is the drag hot spot in?
            function evaluate(drag) {
                const f = drag.y / dragArea.height      // 0 = top edge, 1 = bottom edge

                if (f < window.zoneFraction)
                    reorder(drag.source, false)
                else if (f > 1.0 - window.zoneFraction)
                    reorder(drag.source, true)
                // middle band: deliberately inert (hysteresis)
            }

            // insertBelow == false -> land immediately ABOVE this row
            // insertBelow == true  -> land immediately BELOW this row
            //
            // items.move(from, to) removes at `from` first, so everything
            // below `from` shifts up by one before the insert happens.
            // Guarded so repeated calls with the same result are no-ops.
            function reorder(source, insertBelow) {
                if (!source || source === dragArea)
                    return

                // Direction gate: only the band facing the direction of
                // travel is live. Without this, dragging down one pixel
                // puts the card's bottom edge straight into the next row's
                // TOP band and the gap opens immediately.
                if (insertBelow && source.dragDirection <= 0)
                    return
                if (!insertBelow && source.dragDirection >= 0)
                    return

                const from = source.visualIndex
                const over = dragArea.visualIndex

                let to = over + (insertBelow ? 1 : 0) - (from < over ? 1 : 0)
                to = Math.max(0, Math.min(visualModel.items.count - 1, to))

                if (from !== to)
                    visualModel.items.move(from, to)
            }

            Rectangle {
                id: content

                anchors {
                    horizontalCenter: parent.horizontalCenter
                    verticalCenter: parent.verticalCenter
                }
                width: dragArea.width - window.rowInset * 2
                height: dragArea.height - window.rowInset

                radius: 8
                color: dragArea.held ? "#f2f6fb" : "#ffffff"
                border.width: dragArea.held ? 2 : 1
                border.color: dragArea.held ? dragArea.accent : "#dde3ea"
                scale: dragArea.held ? 1.03 : 1.0
                opacity: dragArea.held ? 0.96 : 1.0

                Behavior on color   { ColorAnimation  { duration: 120 } }
                Behavior on scale   { NumberAnimation { duration: 120; easing.type: Easing.OutQuad } }
                Behavior on opacity { NumberAnimation { duration: 120 } }

                onYChanged: if (dragArea.held) dragArea.trackDirection(mapToItem(null, 0, 0).y)

                // Drag events are only emitted while Drag.active is true.
                Drag.active: dragArea.held
                Drag.source: dragArea
                Drag.keys: ["reorder"]

                // THE TRIGGER POINT: the leading edge of the card, not its
                // centre. Moving down -> bottom edge; moving up -> top edge.
                // Per the Drag docs, "Changes to hotSpot trigger a new drag
                // move with the updated position", so a direction flip takes
                // effect immediately rather than on the next mouse move.
                Drag.hotSpot.x: width / 2
                Drag.hotSpot.y: dragArea.dragDirection < 0 ? 0 : height

                // While held: detach from anchors and reparent out of the
                // view so the item can move freely and draws above the list.
                states: State {
                    when: dragArea.held

                    ParentChange {
                        target: content
                        parent: window.contentItem
                    }
                    AnchorChanges {
                        target: content
                        anchors {
                            horizontalCenter: undefined
                            verticalCenter: undefined
                        }
                    }
                    PropertyChanges {
                        target: content
                        z: 2
                    }
                }

                Rectangle {                     // colour stripe
                    id: stripe
                    anchors {
                        left: parent.left
                        top: parent.top
                        bottom: parent.bottom
                        margins: 1
                    }
                    width: 6
                    radius: 3
                    color: dragArea.accent
                }

                Column {
                    anchors {
                        left: stripe.right
                        right: grip.left
                        verticalCenter: parent.verticalCenter
                        leftMargin: 14
                        rightMargin: 14
                    }
                    spacing: 2

                    Text {
                        width: parent.width
                        text: dragArea.name
                        font.pixelSize: 16
                        font.bold: true
                        elide: Text.ElideRight
                        color: "#1f2933"
                    }
                    Text {
                        width: parent.width
                        text: dragArea.detail
                        font.pixelSize: 12
                        font.italic: true
                        elide: Text.ElideRight
                        color: "#7b8794"
                    }
                }

                Column {                        // drag grip affordance
                    id: grip
                    anchors {
                        right: parent.right
                        rightMargin: 16
                        verticalCenter: parent.verticalCenter
                    }
                    spacing: 3

                    Repeater {
                        model: 3
                        delegate: Rectangle {
                            width: 18
                            height: 2
                            radius: 1
                            color: dragArea.held ? dragArea.accent : "#b3bcc6"
                        }
                    }
                }
            }

            // ---- trigger zone --------------------------------------------
            // ONE full-height DropArea; the 25% bands are a computation on
            // drag.y, not geometry. DragEvent.x/y are local to the DropArea
            // (qquickdroparea.cpp sets them from QDragMoveEvent::pos()), so
            // drag.y / height is the fraction into this row.
            //
            // Full-height matters: with two 25% DropAreas the middle 50% of
            // every row had no drop target at all, so onDropped/containsDrag/
            // exited were unusable for anything (e.g. commit-on-release).
            //
            // positionChanged is handled as well as entered because after a
            // swap the rows animate underneath a cursor that may be perfectly
            // still. reorder() is idempotent, so the extra calls are free.

            DropArea {
                id: dropZone

                anchors.fill: parent
                keys: ["reorder"]

                onEntered: (drag) => dragArea.evaluate(drag)
                onPositionChanged: (drag) => dragArea.evaluate(drag)
            }

            // Optional: uncomment to see the trigger bands while tuning.
            // Rectangle {
            //     anchors { left: parent.left; right: parent.right; top: parent.top }
            //     height: parent.height * window.zoneFraction
            //     color: "#3300ff00"
            // }
            // Rectangle {
            //     anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
            //     height: parent.height * window.zoneFraction
            //     color: "#33ff0000"
            // }
        }
    }

    ListView {
        id: view

        anchors.fill: parent
        anchors.margins: 4
        clip: true

        model: visualModel

        // Spacing is 0 on purpose: the visual gutter lives inside the
        // delegate (rowInset). Real ListView spacing creates dead bands
        // between the DropAreas where the drop target is lost.
        spacing: 0
        cacheBuffer: 200

        // THIS is the gap animation. `displaced` is the generic fallback
        // for addDisplaced / moveDisplaced / removeDisplaced, so a model
        // move makes every other row slide to its new slot.
        displaced: Transition {
            NumberAnimation {
                properties: "x,y"
                duration: window.gapDuration
                easing.type: Easing.OutQuad
            }
        }

        // No `move` transition: the moved row is the one under the cursor,
        // and its visible content is reparented out of the view, so
        // animating its empty delegate root only lags the snap-back.

        ScrollBar.vertical: ScrollBar { }
    }
}
