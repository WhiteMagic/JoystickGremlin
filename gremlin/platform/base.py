# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Abstract base classes for the platform abstraction layer.

Each concrete platform implementation (windows/, linux/) must provide
classes that are compatible with these interfaces.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


# ---------------------------------------------------------------------------
# Keyboard
# ---------------------------------------------------------------------------

class AbstractKey(ABC):
    """Represents a single keyboard key."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def scan_code(self) -> int: ...

    @property
    @abstractmethod
    def is_extended(self) -> bool: ...

    @property
    @abstractmethod
    def virtual_code(self) -> int: ...


class AbstractKeyboardBackend(ABC):
    @abstractmethod
    def send_key_down(self, key: AbstractKey) -> None: ...

    @abstractmethod
    def send_key_up(self, key: AbstractKey) -> None: ...

    @abstractmethod
    def key_from_name(self, name: str) -> AbstractKey: ...

    @abstractmethod
    def key_from_code(self, scan_code: int, is_extended: bool) -> AbstractKey: ...


# ---------------------------------------------------------------------------
# Mouse
# ---------------------------------------------------------------------------

class AbstractMouseBackend(ABC):
    @abstractmethod
    def mouse_relative_motion(self, dx: int, dy: int) -> None: ...

    @abstractmethod
    def mouse_press(self, button: object) -> None: ...

    @abstractmethod
    def mouse_release(self, button: object) -> None: ...

    @abstractmethod
    def mouse_wheel(self, motion: int) -> None: ...


# ---------------------------------------------------------------------------
# Event hooks
# ---------------------------------------------------------------------------

class AbstractKeyboardHook(ABC):
    @abstractmethod
    def register(self, callback: Callable) -> None: ...

    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...


class AbstractMouseHook(ABC):
    @abstractmethod
    def register(self, callback: Callable) -> None: ...

    @abstractmethod
    def start(self) -> None: ...

    @abstractmethod
    def stop(self) -> None: ...


# ---------------------------------------------------------------------------
# Process backend
# ---------------------------------------------------------------------------

class AbstractProcessBackend(ABC):
    """Platform-specific process detection queries.

    Implementations are stateless from the caller's perspective: each call
    to get_active_process_path() returns the current foreground process path.
    Backends may cache intermediate results (e.g. the last seen PID) as
    private implementation details to avoid redundant OS calls.
    """

    @abstractmethod
    def get_active_process_path(self) -> str | None:
        """Return the executable path of the currently focused process.

        Returns None when the path cannot be determined.
        """

    @abstractmethod
    def list_process_paths(self) -> list[str]:
        """Return a sorted, deduplicated list of all running executable paths."""


# ---------------------------------------------------------------------------
# TTS
# ---------------------------------------------------------------------------

class AbstractTextToSpeech(ABC):
    @abstractmethod
    def speak(self, text: str) -> None: ...

    @abstractmethod
    def set_volume(self, value: float) -> None: ...

    @abstractmethod
    def set_rate(self, value: int) -> None: ...


# ---------------------------------------------------------------------------
# Application backend
# ---------------------------------------------------------------------------

class AbstractAppBackend(ABC):
    """Platform-specific application-level configuration."""

    @abstractmethod
    def configure_app(self, app_id: str) -> None:
        """Set the platform application identifier.

        On Windows: sets the App User Model ID (AUMID) used by the taskbar
        and notification centre to group windows and identify the application.
        On Linux: future implementation via XDG App ID / DBus
        (org.freedesktop.Application or xdg-shell app-id under Wayland).
        """

    @abstractmethod
    def font_family(self) -> str:
        """Return the preferred font family name for this platform.

        An empty string means 'use the Qt/system default'.
        This is the hook for eventual user font customisation.
        """

    @abstractmethod
    def user_data_dir(self) -> Path:
        """Return the root directory for Joystick Gremlin user data.

        On Windows: %USERPROFILE%\\Joystick Gremlin
        On Linux:   ~/.config/joystick-gremlin (XDG) or ~/Joystick Gremlin
        """

    @abstractmethod
    def temp_dir(self) -> Path:
        """Return a suitable directory for temporary files."""

    @abstractmethod
    def is_user_admin(self) -> bool:
        """Return True if the current user has administrator/root privileges."""

    @abstractmethod
    def ansi_code_page(self) -> str:
        """Return the ANSI encoding name used to decode device strings.

        On Windows: the active ANSI code page (e.g. 'cp1252').
        On Linux: 'utf-8' (device names from evdev are always UTF-8).
        """

    @abstractmethod
    def executable_file_filter(self) -> str:
        """Return the FileDialog name-filter string for executable files.

        On Windows: restricts selection to .exe files.
        On Linux: all files are permitted (any file can be a script or binary).
        """
