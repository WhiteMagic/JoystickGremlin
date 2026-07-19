# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import win32api
import win32con
import win32gui
from PySide6 import QtGui

import gremlin.util
from gremlin.config import Configuration
from gremlin.ui.backend import Backend

# Private window message the tray icon uses to report mouse activity back to
# our helper window.
_WM_TRAY = win32con.WM_USER + 20

# Shell_NotifyIcon values that pywin32 does not expose as constants.
# Opting into version 4 unlocks the modern notification protocol (cursor
# position packed into wparam, keyboard selection events, better multi-monitor
# menu placement); NIF_SHOWTIP opts into the standard tooltip even when the
# user has balloon tips suppressed by policy.
_NOTIFYICON_VERSION_4 = 4
_NIF_SHOWTIP = 0x00000080
# Keyboard-driven notifications delivered under version 4 (low word of lparam).
_NIN_SELECT = win32con.WM_USER + 0
_NIN_KEYSELECT = win32con.WM_USER + 1

# Tray menu command identifiers.
_ID_SHOW = 1023
_ID_TOGGLE = 1024
_ID_QUIT = 1025


class SystemTrayIcon:

    """System tray presence for Joystick Gremlin built on the Win32
    Shell_NotifyIcon API via pywin32.

    Gremlin is moving away from any QtWidgets dependency, so the tray can't be a
    QSystemTrayIcon (QtWidgets, as is the QML tray fallback). It talks to the
    Windows shell directly instead, via pywin32 which Gremlin already requires.
    Window show/hide still goes through the QML window, a QWindow that lives in
    QtGui rather than QtWidgets.

    When the minimize-to-tray option is enabled, minimizing the main window
    hides it into the tray instead of the taskbar; clicking the icon restores
    it. The tray menu offers profile activate/deactivate and quit, and the icon
    reflects whether a profile is currently active.
    """

    def __init__(self, window: QtGui.QWindow) -> None:
        """Creates the tray icon and starts watching the window.

        Args:
            window: the main application window to hide and restore
        """
        self._window = window
        self._config = Configuration()
        self._backend = Backend()

        self._idle_icon = self._load_icon("gfx/icon.ico")
        self._active_icon = self._load_icon("gfx/icon_active.ico")

        # A hidden helper window receives the icon's mouse-event and menu
        # messages. It is a normal (not message-only) window so it also hears
        # the "TaskbarCreated" broadcast and can re-add the icon if Explorer
        # restarts. Its messages are pumped by Qt's running event loop.
        self._taskbar_created = win32gui.RegisterWindowMessage("TaskbarCreated")
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "JoystickGremlinTray"
        wc.lpfnWndProc = {
            _WM_TRAY: self._on_tray_event,
            win32con.WM_COMMAND: self._on_command,
            win32con.WM_DESTROY: self._on_destroy,
            self._taskbar_created: self._on_taskbar_created,
        }
        self._class_atom = win32gui.RegisterClass(wc)
        # WS_EX_TOOLWINDOW keeps the helper window out of the taskbar and
        # Alt+Tab; WS_EX_NOACTIVATE stops it stealing focus. Together they
        # ensure the zero-size helper can never flicker into view.
        self._hwnd = win32gui.CreateWindowEx(
            win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_NOACTIVATE,
            self._class_atom, "Joystick Gremlin", win32con.WS_OVERLAPPED,
            0, 0, 0, 0, 0, 0, wc.hInstance, None
        )
        self._add_icon()

        self._window.visibilityChanged.connect(self._on_visibility_changed)
        self._backend.activityChanged.connect(self._refresh_icon)

    def remove(self) -> None:
        """Removes the tray icon and helper window (call on shutdown).

        DestroyWindow dispatches WM_DESTROY synchronously, and its handler is
        the sole owner of the icon removal, so tearing down the window here is
        enough -- deleting the icon as well would double-delete it.
        """
        win32gui.DestroyWindow(self._hwnd)

    def restore(self) -> None:
        """Restores and focuses the main window."""
        self._window.showNormal()
        self._window.raise_()
        self._window.requestActivate()

    def _load_icon(self, relative_path: str) -> int:
        """Loads an .ico at the system tray icon size."""
        size = win32api.GetSystemMetrics(win32con.SM_CXSMICON)
        return win32gui.LoadImage(
            0, gremlin.util.resource_path(relative_path), win32con.IMAGE_ICON,
            size, size, win32con.LR_LOADFROMFILE
        )

    def _current_icon(self) -> int:
        active = self._backend.gremlinActive
        return self._active_icon if active else self._idle_icon

    def _add_icon(self) -> None:
        win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, (
            self._hwnd, 0,
            win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
            | _NIF_SHOWTIP,
            _WM_TRAY, self._current_icon(), "Joystick Gremlin"
        ))
        # Select the modern notification behaviour. Must follow NIM_ADD; the
        # version is carried in the timeout/version field of the data tuple.
        win32gui.Shell_NotifyIcon(win32gui.NIM_SETVERSION, (
            self._hwnd, 0, 0, 0, 0, "", "", _NOTIFYICON_VERSION_4
        ))

    def _refresh_icon(self) -> None:
        """Keeps the icon in sync with the profile activation state."""
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, (
            self._hwnd, 0, win32gui.NIF_ICON, _WM_TRAY, self._current_icon()
        ))

    def _on_visibility_changed(
        self,
        visibility: QtGui.QWindow.Visibility
    ) -> None:
        """Hides the window to the tray when minimized, if the option is set."""
        if visibility == QtGui.QWindow.Visibility.Minimized and \
                self._config.value("global", "general", "minimize-to-tray"):
            self._window.hide()

    def _on_tray_event(
        self, hwnd: int, msg: int, wparam: int, lparam: int
    ) -> int:
        """Restores on a left click / double click / keyboard selection of the
        icon, and shows the context menu on a right click / menu key."""
        # Under NOTIFYICON_VERSION_4 the notification event is the low word of
        # lparam; the high word holds the icon id.
        event = lparam & 0xFFFF
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

    def _on_command(
        self, hwnd: int, msg: int, wparam: int, lparam: int
    ) -> int:
        """Dispatches a tray menu selection."""
        command = wparam & 0xFFFF
        if command == _ID_SHOW:
            self._toggle_visibility()
        elif command == _ID_TOGGLE:
            self._backend.toggleActiveState()
        elif command == _ID_QUIT:
            self._quit()
        return 0

    def _toggle_visibility(self) -> None:
        """Hides the window into the tray when it is visible, and restores it
        when it is hidden."""
        if self._window.isVisible():
            self._window.hide()
        else:
            self.restore()

    def _on_taskbar_created(
        self, hwnd: int, msg: int, wparam: int, lparam: int
    ) -> int:
        """Re-adds the icon after an Explorer restart."""
        self._add_icon()
        return 0

    def _on_destroy(
        self, hwnd: int, msg: int, wparam: int, lparam: int
    ) -> int:
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self._hwnd, 0))
        return 0

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
        win32gui.AppendMenu(menu, win32con.MF_STRING, _ID_QUIT, "Quit")

        # TrackPopupMenu needs the owning window in the foreground to dismiss
        # correctly, plus a follow-up message after it returns (a documented
        # Win32 quirk).
        x, y = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self._hwnd)
        win32gui.TrackPopupMenu(
            menu,
            win32con.TPM_LEFTALIGN | win32con.TPM_RIGHTBUTTON,
            x, y, 0, self._hwnd, None
        )
        win32gui.PostMessage(self._hwnd, win32con.WM_NULL, 0, 0)
        win32gui.DestroyMenu(menu)

    def _quit(self) -> None:
        """Quits via the window's close path so unsaved changes are flagged."""
        self.restore()
        self._window.close()
