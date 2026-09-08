# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import contextlib
import ctypes
import logging

import win32api
import win32con
import win32gui
from PySide6 import (
    QtCore,
    QtGui,
)

import gremlin.util
from gremlin.config import Configuration
from gremlin.ui.backend import Backend

# Private message the tray icon uses to report activity to the helper window.
_WM_TRAY = win32con.WM_USER + 20

# Shell_NotifyIcon values pywin32 does not expose.
# https://learn.microsoft.com/en-us/windows/win32/api/shellapi/ns-shellapi-notifyicondataw
_NOTIFYICON_VERSION_4 = 4
_NIF_SHOWTIP = 0x00000080

# Tray menu command identifiers.
_ID_SHOW = 1023
_ID_TOGGLE = 1024
_ID_QUIT = 1025


def _extract_screen_coordinates(wparam: int) -> tuple[int, int]:
    """Returns the screen position packed into a message parameter.

    Args:
        wparam: parameter to extract the position from

    Returns:
        The x and y coordinates contained in the parameter
    """
    # Coordinates are signed, monitors left of or above the primary one yield
    # negative values.
    return (ctypes.c_short(wparam).value, ctypes.c_short(wparam >> 16).value)


class SystemTrayIcon(QtCore.QObject):
    """Tray icon for Gremlin, implemented using Win32 functionality.

    Supports hiding the Gremlin UI to the system tray on minimize and close. The context
    menu exposes basic UI functionality. The icon reflects Gremlin's activation state.
    """

    def __init__(self, window: QtGui.QWindow) -> None:
        """Creates the tray icon and starts monitoring the window.

        Args:
            window: the main application window to hide and restore
        """
        super().__init__()

        self._window = window
        self._backend = Backend()
        self._icon_present = False
        self._last_window_mode = QtGui.QWindow.Visibility.Windowed
        self._taskbar_created = 0
        self._instance = 0
        self._class_atom = None
        self._hwnd = 0
        self._idle_icon = 0
        self._active_icon = 0

        # Failure to acquire the resources needed for the system tray should not crash
        # Gremlin, but only disable the system tray icon.
        try:
            self._create_resources()
        except win32gui.error as e:
            logging.getLogger("system").warning(
                f"Failed to create the system tray icon: {e.strerror}"
            )
            return

        self._window.visibilityChanged.connect(self._window_mode_changed_cb)
        self._backend.activityChanged.connect(self._gremlin_status_change_cb)
        # QML's closing signal carries a QQuickCloseEvent, a type PySide cannot
        # convert, so closing is intercepted via the window's events instead.
        self._window.installEventFilter(self)

        # Ensure the window's visibility information is correctly capture, as the window
        # is not guaranteed to be visible on launch.
        self._window_mode_changed_cb(self._window.visibility())

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Hides the window into the tray instead of closing it.

        Args:
            watched: object the event is delivered to
            event: event being delivered

        Returns:
            True if the event was handled and is not to be delivered
        """
        # Quitting goes through Qt.quit, so a close is always the user
        # dismissing the window, which without an icon could not be undone.
        if (
            event.type() == QtCore.QEvent.Type.Close
            and self._icon_present
            and Configuration().value("global", "general", "close-to-tray")
        ):
            event.ignore()
            self._window.hide()
            return True
        return super().eventFilter(watched, event)

    def release_resources(self) -> None:
        """Destroys the tray icon and its helper window."""
        # Each resource is released independently and the system may already have
        # reclaimed a handle, which must not stop the remaining cleanup.
        if self._hwnd:
            with contextlib.suppress(win32gui.error):
                win32gui.DestroyWindow(self._hwnd)
            self._hwnd = 0
        if self._class_atom is not None:
            with contextlib.suppress(win32gui.error):
                win32gui.UnregisterClass(self._class_atom, self._instance)
            self._class_atom = None
        for icon in (self._idle_icon, self._active_icon):
            if icon:
                with contextlib.suppress(win32gui.error):
                    win32gui.DestroyIcon(icon)
        self._idle_icon = 0
        self._active_icon = 0

    def restore_window(self) -> None:
        """Shows and focuses the main window in its previous state."""
        self._window.setVisibility(self._last_window_mode)
        self._window.raise_()
        self._window.requestActivate()

    def _create_resources(self) -> None:
        """Creates the resources needed by the system tray icon.

        Failures in this call will cause a win32gui.error to be raised, that the called
        has to handle.
        """
        self._idle_icon = self._create_icon("gfx/icon.ico")
        self._active_icon = self._create_icon("gfx/icon_active.ico")

        # The system tray messages need a window to be delivered to. A plain window
        # is used instead of a message-only one, as that would not receive the
        # "TaskbarCreated" broadcast. The event loop is driven by Qt's event loop.
        self._taskbar_created = win32gui.RegisterWindowMessage("TaskbarCreated")
        self._instance = win32api.GetModuleHandle(None)
        wc = win32gui.WNDCLASS()
        wc.hInstance = self._instance
        wc.lpszClassName = "JoystickGremlinSystemTray"
        wc.lpfnWndProc = {
            _WM_TRAY: self._system_tray_event_cb,
            win32con.WM_COMMAND: self._handle_context_menu_cb,
            win32con.WM_DESTROY: self._destroy_system_tray_cb,
            self._taskbar_created: self._taskbar_created_cb,
        }
        self._class_atom = win32gui.RegisterClass(wc)
        # Keep the zero-size helper out of the taskbar and Alt+Tab and prevent
        # it taking focus.
        self._hwnd = win32gui.CreateWindowEx(
            win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_NOACTIVATE,
            self._class_atom,
            "Joystick Gremlin",
            win32con.WS_OVERLAPPED,
            0,
            0,
            0,
            0,
            0,
            0,
            wc.hInstance,
            None,
        )
        self._add_icon()

    def _create_icon(self, relative_path: str) -> int:
        """Loads an icon at the size used by the tray.

        Args:
            relative_path: path to the .ico file, relative to the resource root

        Returns:
            Handle of the loaded icon
        """
        size = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        return win32gui.LoadImage(
            0,
            gremlin.util.resource_path(relative_path),
            win32con.IMAGE_ICON,
            size,
            size,
            win32con.LR_LOADFROMFILE,
        )

    def _current_icon(self) -> int:
        """Returns the icon handle matching Gremlin's activation state.

        Returns:
            Handle of the icon to display
        """
        return self._active_icon if self._backend.gremlinActive else self._idle_icon

    def _add_icon(self) -> None:
        """Adds the icon to the tray using notify protocol v4."""
        # Icon creation can fail if the shell is still being built. In that case the
        # TaskbarCreated broadcast offers a second chance to create the icon.
        try:
            win32gui.Shell_NotifyIcon(
                win32gui.NIM_ADD,
                (
                    self._hwnd,
                    0,
                    win32gui.NIF_ICON
                    | win32gui.NIF_MESSAGE
                    | win32gui.NIF_TIP
                    | _NIF_SHOWTIP,
                    _WM_TRAY,
                    self._current_icon(),
                    "Joystick Gremlin",
                ),
            )
            win32gui.Shell_NotifyIcon(
                win32gui.NIM_SETVERSION,
                (self._hwnd, 0, 0, 0, 0, "", "", _NOTIFYICON_VERSION_4),
            )
            self._icon_present = True
        except win32gui.error:
            self._icon_present = False
            logging.getLogger("system").warning(
                "Failed to add the system tray icon", exc_info=True
            )

    def _gremlin_status_change_cb(self) -> None:
        """Updates the icon to match Gremlin's activation state."""
        with contextlib.suppress(win32gui.error):
            win32gui.Shell_NotifyIcon(
                win32gui.NIM_MODIFY,
                (self._hwnd, 0, win32gui.NIF_ICON, _WM_TRAY, self._current_icon()),
            )

    def _window_mode_changed_cb(self, mode: QtGui.QWindow.Visibility) -> None:
        """Hides the window into the tray when it is minimized.

        Args:
            mode: the window's new visibility mode
        """
        # Store the mode to the restore the UI to when it's not minimized.
        if mode in (
            QtGui.QWindow.Visibility.Windowed,
            QtGui.QWindow.Visibility.Maximized,
            QtGui.QWindow.Visibility.FullScreen,
        ):
            self._last_window_mode = mode

        # If the icon failed to load, i.e. we have no system tray, we minimize to the
        # taskbar unconditionally, to keep the Gremlin UI accessible.
        if (
            mode == QtGui.QWindow.Visibility.Minimized
            and self._icon_present
            and Configuration().value("global", "general", "minimize-to-tray")
        ):
            self._window.hide()

    def _system_tray_event_cb(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        """Handles mouse interactions with the system tray icon.

        Restores the window on a left click of the icon, a right click shows the
        context menu. Only mouse interaction is supported.

        Args:
            hwnd: handle of the window receiving the message
            msg: message identifier
            wparam: anchor position, packed
            lparam: notification event and icon id, packed

        Returns:
            0, the message has been handled
        """
        match win32api.LOWORD(lparam):
            case win32con.WM_LBUTTONUP:
                self.restore_window()
            case win32con.WM_RBUTTONUP:
                self._show_menu(*_extract_screen_coordinates(wparam))
        return 0

    def _handle_context_menu_cb(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        """Dispatches a tray menu selection.

        Args:
            hwnd: handle of the window receiving the message
            msg: message identifier
            wparam: menu command identifier, packed
            lparam: unused

        Returns:
            0, the message has been handled
        """
        command = win32api.LOWORD(wparam)
        if command == _ID_SHOW:
            self._toggle_visibility()
        elif command == _ID_TOGGLE:
            self._backend.toggleActiveState()
        elif command == _ID_QUIT:
            self._quit_gremlin()
        return 0

    def _toggle_visibility(self) -> None:
        """Hides the window when it is visible and restores it when hidden."""
        self._window.hide() if self._window.isVisible() else self.restore_window()

    def _taskbar_created_cb(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        """Re-adds the icon after Explorer restarts.

        Args:
            hwnd: handle of the window receiving the message
            msg: message identifier
            wparam: unused
            lparam: unused

        Returns:
            0, the message has been handled
        """
        if self._icon_present:
            self._delete_icon()
        self._add_icon()
        return 0

    def _destroy_system_tray_cb(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        """Removes the icon as the helper window is destroyed.

        Args:
            hwnd: handle of the window receiving the message
            msg: message identifier
            wparam: unused
            lparam: unused

        Returns:
            0, the message has been handled
        """
        self._delete_icon()
        return 0

    def _delete_icon(self) -> None:
        """Removes the icon from the tray, if it is currently present."""
        # Deleting an icon the shell no longer knows about raises, but the desired
        # state has been reached either way.
        with contextlib.suppress(win32gui.error):
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self._hwnd, 0))
        self._icon_present = False

    def _show_menu(self, x: int, y: int) -> None:
        """Builds and shows the system tray context menu at the given position.

        Args:
            x: horizontal screen coordinate to anchor the menu at
            y: vertical screen coordinate to anchor the menu at
        """
        menu = win32gui.CreatePopupMenu()
        try:
            show_hide = (
                "Hide Joystick Gremlin"
                if self._window.isVisible()
                else "Show Joystick Gremlin"
            )
            win32gui.AppendMenu(menu, win32con.MF_STRING, _ID_SHOW, show_hide)
            win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
            label = "Deactivate" if self._backend.gremlinActive else "Activate"
            win32gui.AppendMenu(menu, win32con.MF_STRING, _ID_TOGGLE, label)
            win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
            win32gui.AppendMenu(
                menu, win32con.MF_STRING, _ID_QUIT, "Quit Joystick Gremlin"
            )

            # A tray menu needs its owner in the foreground to be dismissed by clicking
            # elsewhere, and a message posted afterwards for the next click on the icon
            # to register. A denied foreground change only costs the dismissal.
            # https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-trackpopupmenu
            with contextlib.suppress(win32gui.error):
                win32gui.SetForegroundWindow(self._hwnd)
            win32gui.TrackPopupMenu(
                menu,
                win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON,
                x,
                y,
                0,
                self._hwnd,
                None,
            )
            win32gui.PostMessage(self._hwnd, win32con.WM_NULL, 0, 0)
        finally:
            win32gui.DestroyMenu(menu)

    def _quit_gremlin(self) -> None:
        """Asks the UI to quit Gremlin.

        Restores the window first, so that the user sees the quit dialog.
        """
        self.restore_window()
        self._backend.quitRequested.emit()
