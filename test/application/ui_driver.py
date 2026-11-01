# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import math
from collections.abc import (
    Callable,
    Sequence,
)

import pytestqt.exceptions
import pytestqt.qtbot
import shiboken6
from PySide6 import (
    QtCore,
    QtGui,
    QtQuick,
)
from PySide6.QtTest import QTest


class UiDriver:
    """Drives the QML UI with mouse and keyboard events sent directly to the QML window.

    Getters returning a single object, such as QQuickItem.window(), bind the wrapper's
    lifetime to the wrapper from which they originated. Calling them on short-lived item
    wrappers invalidates long-lived ones, such as the main window, so the window of each
    item is recorded while walking the item tree.
    """

    def __init__(self, qtbot: pytestqt.qtbot.QtBot) -> None:
        self._qtbot = qtbot
        self._item_windows: dict[int, QtQuick.QQuickWindow] = {}
        self._mouse_press_location: (
            tuple[QtQuick.QQuickWindow, QtCore.QPoint] | None
        ) = None

    def find_item(
        self, name: str, within: QtQuick.QQuickItem | None = None
    ) -> QtQuick.QQuickItem:
        """Waits for exactly one visible item called name and returns it."""
        return self.find_one_where(
            lambda item: item.objectName() == name, f"named '{name}'", within
        )

    def find_object(
        self, name: str, within: QtQuick.QQuickItem | None = None
    ) -> QtCore.QObject:
        """Waits for exactly one visible item or non-item object called name."""
        return self._single(lambda: self.find_all(name, within), f"named '{name}'")

    def find_all(
        self, name: str, within: QtQuick.QQuickItem | None = None
    ) -> list[QtCore.QObject]:
        """Returns all visible items and non-item objects that match the given name."""
        matches: dict[int, QtCore.QObject] = {
            _address(item): item
            for item in self.find_where(lambda item: item.objectName() == name, within)
        }
        # Menus, popups and timers are not items which we don't wrap to avoid issues.
        roots: Sequence[QtCore.QObject] = (
            [within] if within is not None else self._windows()
        )
        for root in roots:
            for obj in root.findChildren(QtCore.QObject, name):
                if not isinstance(obj, QtQuick.QQuickItem):
                    matches[_address(obj)] = obj
        return list(matches.values())

    def find_one_where(
        self,
        predicate: Callable[[QtQuick.QQuickItem], bool],
        description: str,
        within: QtQuick.QQuickItem | None = None,
        visible_only: bool = True,
        stop_at: Callable[[QtQuick.QQuickItem], bool] | None = None,
    ) -> QtQuick.QQuickItem:
        """Waits for exactly one item for which the predicate is true."""
        return self._single(
            lambda: self.find_where(predicate, within, visible_only, stop_at),
            description,
        )

    def find_where(
        self,
        predicate: Callable[[QtQuick.QQuickItem], bool],
        within: QtQuick.QQuickItem | None = None,
        visible_only: bool = True,
        stop_at: Callable[[QtQuick.QQuickItem], bool] | None = None,
    ) -> list[QtQuick.QQuickItem]:
        """Returns all items that match the predicate.

        The selection can be customized by limiting the search to children of a given
        item, to visible items only, and to not descend into children of certain items.
        """
        roots = [within] if within is not None else self._root_items()
        return [
            item
            for item in self._items(roots, visible_only, stop_at)
            if item not in roots and predicate(item)
        ]

    def click(
        self, item: QtQuick.QQuickItem, position: QtCore.QPointF | None = None
    ) -> None:
        """Clicks the item at its center or the given position."""
        self.wait_until(lambda: item.isVisible() and item.isEnabled())
        window = self._window_of(item)
        self._wait_for_frame(window)
        QTest.mouseClick(
            window,
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.KeyboardModifier.NoModifier,
            self._scene_point(item, position),
        )

    def double_click(
        self, item: QtQuick.QQuickItem, position: QtCore.QPointF | None = None
    ) -> None:
        """Double-clicks the item at its center or the given position."""
        self.wait_until(lambda: item.isVisible() and item.isEnabled())
        window = self._window_of(item)
        self._wait_for_frame(window)
        QTest.mouseDClick(
            window,
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.KeyboardModifier.NoModifier,
            self._scene_point(item, position),
        )

    def press(
        self, item: QtQuick.QQuickItem, position: QtCore.QPointF | None = None
    ) -> None:
        """Presses the left button on the item at its center or the given position."""
        self.wait_until(lambda: item.isVisible() and item.isEnabled())
        window = self._window_of(item)
        self._wait_for_frame(window)
        point = self._scene_point(item, position)
        QTest.mousePress(
            window,
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.KeyboardModifier.NoModifier,
            point,
        )
        self._mouse_press_location = (window, point)

    def drag_to(
        self, item: QtQuick.QQuickItem, position: QtCore.QPointF | None = None
    ) -> None:
        """Drags the held mouse to the item's center or to the given position."""
        self._drag_to_scene_point(self._scene_point(item, position))

    def drag_by(self, offset: QtCore.QPointF) -> None:
        """Drags the held mouse by offset."""
        assert self._mouse_press_location is not None, "No mouse button is held"
        _, point = self._mouse_press_location
        self._drag_to_scene_point(point + offset.toPoint())

    def _drag_to_scene_point(self, point: QtCore.QPoint) -> None:
        assert self._mouse_press_location is not None, "No mouse button is held"
        window, _ = self._mouse_press_location
        QTest.mouseMove(window, point)
        self._mouse_press_location = (window, point)
        self._wait_for_frame(window)

    def release(self) -> None:
        """Releases the held mouse button where the mouse is."""
        assert self._mouse_press_location is not None, "No mouse button is held"
        window, point = self._mouse_press_location
        self._mouse_press_location = None
        QTest.mouseRelease(
            window,
            QtCore.Qt.MouseButton.LeftButton,
            QtCore.Qt.KeyboardModifier.NoModifier,
            point,
        )

    def drag_item_from_to(
        self, item: QtQuick.QQuickItem, start: QtCore.QPointF, end: QtCore.QPointF
    ) -> None:
        """Drags from start to end, in item coordinates as of the press."""
        start_point = item.mapToScene(start)
        end_point = item.mapToScene(end)
        # The content item's coordinates are scene coordinates.
        content_item = self._content_item(self._window_of(item))
        step_count = max(
            1,
            math.ceil(
                QtCore.QLineF(start_point, end_point).length()
                / QtGui.QGuiApplication.styleHints().startDragDistance()
            ),
        )
        self.press(item, start)
        for step in range(1, step_count + 1):
            self.drag_to(
                content_item,
                start_point + (end_point - start_point) * (step / step_count),
            )
        self.release()

    def type_text(self, item: QtQuick.QQuickItem, text: str) -> None:
        """Replaces the text of an editable item and confirms it with Return."""
        self.click(item)
        item.forceActiveFocus()
        window = self._window_of(item)
        # Key events only reach items of the active window.
        window.requestActivate()
        self._qtbot.waitActive(window)
        QTest.keyClick(
            window, QtCore.Qt.Key.Key_A, QtCore.Qt.KeyboardModifier.ControlModifier
        )
        # QTest.keyClicks can only send keys to widgets but we're using QML. Thus we
        # have to send actual ASCII key codes as a workaround. Some mangling has to
        # happen to ensure characters are safely converted..
        for character in text:
            QTest.sendKeyEvent(
                QTest.KeyAction.Click,
                window,
                QtCore.Qt.Key(ord(character.upper()))
                if character.isascii()
                else QtCore.Qt.Key.Key_unknown,
                character,
                QtCore.Qt.KeyboardModifier.NoModifier,
            )
        QTest.keyClick(window, QtCore.Qt.Key.Key_Return)

    def key_click(self, key: QtCore.Qt.Key) -> None:
        """Presses and releases key in the window holding the keyboard focus."""
        self.wait_until(
            lambda: isinstance(
                QtGui.QGuiApplication.focusWindow(), QtQuick.QQuickWindow
            )
        )
        QTest.keyClick(QtGui.QGuiApplication.focusWindow(), key)

    def select(self, combo: QtQuick.QQuickItem, text: str) -> None:
        """Opens the combo box's popup and clicks the entry showing text."""
        # The popup property can't be read from Python, but the popup opens in the
        # window's overlay.
        overlay = self.find_one_where(
            lambda item: item.inherits("QQuickOverlay"),
            "being the overlay",
            self._content_item(self._window_of(combo)),
            visible_only=False,
        )
        self.click(combo)
        entry = self._scroll_to_entry(overlay, text)
        self.click(entry)
        # The selection may rebuild the item holding the combo, deleting the combo.
        try:
            self.wait_until(
                lambda: (
                    not shiboken6.isValid(combo)
                    or combo.property("currentText") == text
                )
            )
        except pytestqt.exceptions.TimeoutError:
            pass
        if not shiboken6.isValid(combo):
            return
        is_popup_open = shiboken6.isValid(entry) and entry.isVisible()
        assert combo.property("currentText") == text, (
            f"Combo shows '{combo.property('currentText')}' instead of '{text}', "
            f"popup {'still open' if is_popup_open else 'closed'}"
        )

    def _scroll_to_entry(
        self, overlay: QtQuick.QQuickItem, text: str
    ) -> QtQuick.QQuickItem:
        """Wheels the open popup's list until its entry showing text is visible."""
        popup_list = self.find_one_where(
            lambda item: item.inherits("QQuickListView"),
            "listing the popup's entries",
            overlay,
        )
        self._wait_for_frame(self._window_of(popup_list))

        def shown_entries() -> list[QtQuick.QQuickItem]:
            # Delegates exist a little beyond the list's edges.
            return [
                entry
                for entry in self.find_where(
                    # A delegate's own text is empty, its label is the Text child.
                    lambda item: (
                        item.inherits("QQuickText") and item.property("text") == text
                    ),
                    popup_list,
                )
                if 0 <= entry.mapToItem(popup_list, QtCore.QPointF()).y()
                and entry.mapToItem(popup_list, QtCore.QPointF(0, entry.height())).y()
                <= popup_list.height()
            ]

        # Wheels down to the end first, then up to the beginning, until a step stalls.
        for angle_delta, edge in [(-120, "atYEnd"), (120, "atYBeginning")]:
            previous_y = None
            while (
                not shown_entries()
                and not popup_list.property(edge)
                and popup_list.property("contentY") != previous_y
            ):
                previous_y = popup_list.property("contentY")
                self._wheel(popup_list, angle_delta)
        entries = shown_entries()
        assert len(entries) == 1, (
            f"Expected one popup entry showing '{text}', found {len(entries)}"
        )
        return entries[0]

    def _wheel(self, item: QtQuick.QQuickItem, angle_delta: int) -> None:
        """Turns the mouse wheel over the item's center.

        Positive delta values scroll up.
        """
        window = self._window_of(item)
        point = QtCore.QPointF(self._scene_point(item, None))
        event = QtGui.QWheelEvent(
            point,
            window.mapToGlobal(point),
            QtCore.QPoint(),
            QtCore.QPoint(0, angle_delta),
            QtCore.Qt.MouseButton.NoButton,
            QtCore.Qt.KeyboardModifier.NoModifier,
            QtCore.Qt.ScrollPhase.NoScrollPhase,
            False,
        )
        QtCore.QCoreApplication.sendEvent(window, event)
        self._wait_for_frame(window)

    def choose_menu_item(self, button: QtQuick.QQuickItem, entry: str) -> None:
        """Opens an AddActionMenuButton's menu and clicks the given entry."""
        self.click(button)
        self.click(self.find_item(f"{button.objectName()}_{entry}"))

    def open_menu(self, *titles: str) -> None:
        """Opens a menu bar menu and then its nested submenus, given by title."""
        for title in titles:
            self.click(self._menu_opener(title))

    def close_window(self, item: QtQuick.QQuickItem) -> None:
        """Closes the window holding the item."""
        window = self._window_of(item)
        window.close()
        self.wait_until(lambda: not shiboken6.isValid(window) or not window.isVisible())

    def reset(self, main_window: QtQuick.QQuickWindow) -> None:
        """Releases a held mouse button and closes every window but main_window."""
        if self._mouse_press_location is not None:
            self.release()
        main_address = _address(main_window)
        for window in self._windows():
            if _address(window) != main_address:
                window.close()
        self.wait_until(
            lambda: [_address(window) for window in self._windows()] == [main_address]
        )

    def wait_until(self, predicate: Callable[[], object], timeout: int = 2000) -> None:
        """Waits for the predicate to become true or the timeout to expire."""
        self._qtbot.waitUntil(lambda: bool(predicate()), timeout=timeout)

    def wait_for_value(
        self, getter: Callable[[], object], expected: object, timeout: int = 2000
    ) -> None:
        """Waits for getter to return expected, failing with the last value seen."""
        try:
            self.wait_until(lambda: getter() == expected, timeout)
        except pytestqt.exceptions.TimeoutError:
            pass
        value = getter()
        assert value == expected, f"Expected {expected!r}, found {value!r}"

    @staticmethod
    def _scene_point(
        item: QtQuick.QQuickItem, position: QtCore.QPointF | None
    ) -> QtCore.QPoint:
        """Maps an position from item coordinate to scene coordinates.

        If no point is given the item's center is used.
        """
        if position is None:
            position = QtCore.QPointF(item.width() / 2, item.height() / 2)
        return item.mapToScene(position).toPoint()

    def _wait_for_frame(self, window: QtQuick.QQuickWindow) -> None:
        """Waits for a frame to be drawn."""
        # Views cull new delegates, which then would not any input. They are only drawn
        # once the next "polish" phase has happened.
        with self._qtbot.waitSignal(window.frameSwapped):
            window.update()

    def _menu_opener(self, title: str) -> QtQuick.QQuickItem:
        return self.find_one_where(
            lambda item: (
                (item.inherits("QQuickMenuBarItem") or item.inherits("QQuickMenuItem"))
                and item.property("text") == title
            ),
            f"opening menu '{title}'",
        )

    def _single[T: QtCore.QObject](
        self, lookup: Callable[[], Sequence[T]], description: str
    ) -> T:
        matches: Sequence[T] = []

        def found_one() -> bool:
            nonlocal matches
            matches = lookup()
            return len(matches) == 1

        try:
            self.wait_until(found_one)
        except pytestqt.exceptions.TimeoutError:
            pass
        assert len(matches) == 1, (
            f"Expected one object {description}, found {len(matches)}"
        )
        return matches[0]

    def _root_items(self) -> list[QtQuick.QQuickItem]:
        return [self._content_item(window) for window in self._windows()]

    @staticmethod
    def _windows() -> list[QtQuick.QQuickWindow]:
        # Includes popups opened as windows, and the overlay is inside contentItem.
        return [
            window
            for window in QtGui.QGuiApplication.topLevelWindows()
            if isinstance(window, QtQuick.QQuickWindow) and window.isVisible()
        ]

    def _content_item(self, window: QtQuick.QQuickWindow) -> QtQuick.QQuickItem:
        content_item = window.contentItem()
        self._item_windows[_address(content_item)] = window
        return content_item

    def _window_of(self, item: QtQuick.QQuickItem) -> QtQuick.QQuickWindow:
        return self._item_windows[_address(item)]

    def _items(
        self,
        roots: Sequence[QtQuick.QQuickItem],
        visible_only: bool,
        stop_at: Callable[[QtQuick.QQuickItem], bool] | None = None,
    ) -> list[QtQuick.QQuickItem]:
        # Repeater-created items have no QObject parent, only a parent item.
        items: list[QtQuick.QQuickItem] = []
        pending = [(root, self._window_of(root)) for root in roots]
        while pending:
            item, window = pending.pop()
            # Skips items whose wrapper outlived a deletion.
            if shiboken6.isValid(item) and (item.isVisible() or not visible_only):
                items.append(item)
                self._item_windows[_address(item)] = window
                if item in roots or stop_at is None or not stop_at(item):
                    pending.extend(
                        (child, window) for child in QtQuick.QQuickItem.childItems(item)
                    )
        return items


def _address(obj: QtCore.QObject) -> int:
    return shiboken6.getCppPointer(obj)[0]
