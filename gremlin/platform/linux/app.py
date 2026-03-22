# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Linux application backend."""

import os
from pathlib import Path
import tempfile

from gremlin.platform.base import AbstractAppBackend


class AppBackend(AbstractAppBackend):

    """Linux implementation of application-level platform configuration."""

    # Number of virtual joystick (vjoy) devices pre-created at startup.
    # Increase this if you need more than 4 virtual devices.
    vjoy_device_count: int = 4

    def configure_app(self, app_id: str) -> None:
        """No-op on Linux: Qt propagates the app-id to the compositor via
        QApplication.setApplicationName(), called by the main application."""

    def font_family(self) -> str:
        """Return empty string to let Qt use the desktop environment's font."""
        return ""

    def user_data_dir(self) -> Path:
        """Returns ~/Joystick Gremlin (XDG migration can be done later)."""
        return Path.home() / "Joystick Gremlin"

    def temp_dir(self) -> Path:
        """Returns the system temporary directory."""
        return Path(tempfile.gettempdir())

    def is_user_admin(self) -> bool:
        """Returns True if the process runs as root (uid 0)."""
        return os.geteuid() == 0

    def ansi_code_page(self) -> str:
        """Device names from evdev are always UTF-8."""
        return "utf-8"

    def executable_file_filter(self) -> str:
        """Any file can be an executable on Linux."""
        return "Executable files (*)"
