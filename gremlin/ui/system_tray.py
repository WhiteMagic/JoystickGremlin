# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import contextlib

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

"""Shell_NotifyIcon values pywin32 does not expose.

https://learn.microsoft.com/en-us/windows/win32/api/shellapi/ns-shellapi-notifyicondataw
"""
_NOTIFYICON_VERSION_4 = 4
_NIF_SHOWTIP = 0x00000080
_NIN_SELECT = win32con.WM_USER + 0
_NIN_KEYSELECT = win32con.WM_USER + 1

# Tray menu command identifiers.
_ID_SHOW = 1023
_ID_TOGGLE = 1024
_ID_QUIT = 1025


def _low_word(value: int) -> int:
    """Returns the low 16 bits of a message parameter.

    Args:
        value: parameter to extract the low word from

    Returns:
        The parameter's low word
    """
    return value & 0xFFFF


class SystemTrayIcon(QtCore.QObject):
    """Tray icon for Gremlin, implemented via Shell_NotifyIcon.

    Optionally hides the main window into the tray on minimize and on close,
    restoring it when the icon is activated. The menu allows toggling the
    window's visibility, activating and deactivating the profile, and quitting,
    while the icon reflects whether a profile is currently active.
    """

    def __init__(self, window: QtGui.QWindow) -> None:
        """Creates the tray icon and starts watching the window.

        Args:
            window: the main application window to hide and restore
        """
        super().__init__()

        self._window = window
        self._backend = Backend()
        self._icon_present = False
        self._quitting = False

        self._idle_icon = self._create_icon("gfx/icon.ico")
        self._active_icon = self._create_icon("gfx/icon_active.ico")

        # The icon's messages need a window to be delivered to. A plain window
        # rather than a message-only one, as those don't receive the
        # "TaskbarCreated" broadcast. Qt's event loop pumps its messages.
        self._taskbar_created = win32gui.RegisterWindowMessage("TaskbarCreated")
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "JoystickGremlinTray"
        wc.lpfnWndProc = {
            _WM_TRAY: self._tray_event_cb,
            win32con.WM_COMMAND: self._command_cb,
            win32con.WM_DESTROY: self._destroy_cb,
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

        self._window.visibilityChanged.connect(self._visibility_changed_cb)
        self._backend.activityChanged.connect(self._activity_changed_cb)
        # QML's closing signal carries a QQuickCloseEvent, a type PySide cannot
        # convert, so closing is intercepted via the window's events instead.
        self._window.installEventFilter(self)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Hides the window into the tray instead of closing it.

        Args:
            watched: object the event is delivered to
            event: event being delivered

        Returns:
            True if the event was handled and is not to be delivered
        """
        # Quitting from the tray menu closes the window deliberately and has to
        # remain a close.
        if (
            event.type() == QtCore.QEvent.Type.Close
            and not self._quitting
            and Configuration().value("global", "general", "close-to-tray")
        ):
            event.ignore()
            self._window.hide()
            return True
        return super().eventFilter(watched, event)

    def remove(self) -> None:
        """Destroys the tray icon and its helper window."""
        # The WM_DESTROY handler removes the icon.
        win32gui.DestroyWindow(self._hwnd)

    def restore(self) -> None:
        """Shows and focuses the main window."""
        self._window.showNormal()
        self._window.raise_()
        self._window.requestActivate()

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
        # v4 has to be requested after the icon exists. It packs the event into
        # lparam's low word and adds keyboard selection events. NIF_SHOWTIP
        # forces the standard tooltip even where policy suppresses tips.
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

    def _activity_changed_cb(self) -> None:
        """Updates the icon to match Gremlin's activation state."""
        win32gui.Shell_NotifyIcon(
            win32gui.NIM_MODIFY,
            (self._hwnd, 0, win32gui.NIF_ICON, _WM_TRAY, self._current_icon()),
        )

    def _visibility_changed_cb(self, visibility: QtGui.QWindow.Visibility) -> None:
        """Hides the window into the tray when it is minimized.

        Args:
            visibility: the window's new visibility state
        """
        if visibility == QtGui.QWindow.Visibility.Minimized and Configuration().value(
            "global", "general", "minimize-to-tray"
        ):
            self._window.hide()

    def _tray_event_cb(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        """Handles tray icon interactions.

        Restores on a left click, double click, or keyboard selection of the
        icon. Right click or menu key display the context menu.

        Args:
            hwnd: handle of the window receiving the message
            msg: message identifier
            wparam: cursor position, packed
            lparam: notification event and icon id, packed

        Returns:
            0, the message has been handled
        """
        event = _low_word(lparam)
        if event in (
            win32con.WM_LBUTTONUP,
            win32con.WM_LBUTTONDBLCLK,
            _NIN_SELECT,
            _NIN_KEYSELECT,
        ):
            self.restore()
        elif event in (win32con.WM_RBUTTONUP, win32con.WM_CONTEXTMENU):
            self._show_menu()
        return 0

    def _command_cb(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        """Dispatches a tray menu selection.

        Args:
            hwnd: handle of the window receiving the message
            msg: message identifier
            wparam: menu command identifier, packed
            lparam: unused

        Returns:
            0, the message has been handled
        """
        command = _low_word(wparam)
        if command == _ID_SHOW:
            self._toggle_visibility()
        elif command == _ID_TOGGLE:
            self._backend.toggleActiveState()
        elif command == _ID_QUIT:
            self._quit_gremlin()
        return 0

    def _toggle_visibility(self) -> None:
        """Hides the window when it is visible and restores it when hidden."""
        if self._window.isVisible():
            self._window.hide()
        else:
            self.restore()

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
        # Explorer restarting discards every tray icon, however the broadcast is
        # not guaranteed to follow one, and adding twice leaves a dead icon
        # behind. Remove any icon we still believe in first.
        if self._icon_present:
            self._delete_icon()
        self._add_icon()
        return 0

    def _destroy_cb(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
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
        # Deleting an icon the shell no longer knows about raises, which is
        # harmless as the desired state has been reached either way.
        with contextlib.suppress(win32gui.error):
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self._hwnd, 0))
        self._icon_present = False

    def _show_menu(self) -> None:
        """Builds and shows the tray context menu at the cursor."""
        menu = win32gui.CreatePopupMenu()
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
        win32gui.AppendMenu(menu, win32con.MF_STRING, _ID_QUIT, "Quit Joystick Gremlin")

        # A tray menu needs its owner in the foreground to be dismissed by
        # clicking elsewhere, and a message posted afterwards for the next click
        # on the icon to register.
        # https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-trackpopupmenu
        x, y = win32gui.GetCursorPos()
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
        win32gui.DestroyMenu(menu)

    def _quit_gremlin(self) -> None:
        """Quits Gremlin via the window's close path."""
        # Showing the window first so the unsaved changes prompt is visible.
        self._quitting = True
        self.restore()
        self._window.close()
        self._quitting = False
