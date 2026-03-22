# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Windows application backend."""

import ctypes
import os
from pathlib import Path

from gremlin.platform.base import AbstractAppBackend


class AppBackend(AbstractAppBackend):

    """Windows implementation of application-level platform configuration."""

    def configure_app(self, app_id: str) -> None:
        """Set the App User Model ID (AUMID) for the Windows taskbar.

        The AUMID controls how Windows groups application windows in the
        taskbar and identifies the application for notifications and
        jump-list pinning.

        Args:
            app_id: the application identifier string (e.g. "joystick.gremlin")
        """
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)

    def font_family(self) -> str:
        """Segoe UI is the standard Windows UI typeface."""
        return "Segoe UI"

    def user_data_dir(self) -> Path:
        """Returns %USERPROFILE%\\Joystick Gremlin."""
        return Path(os.environ["USERPROFILE"]) / "Joystick Gremlin"

    def temp_dir(self) -> Path:
        """Returns the %TEMP% directory."""
        return Path(os.environ["TEMP"])

    def is_user_admin(self) -> bool:
        """Returns True if the process has administrator privileges."""
        return ctypes.windll.shell32.IsUserAnAdmin() == 1

    def ansi_code_page(self) -> str:
        """Returns the active Windows ANSI code page (e.g. 'cp1252')."""
        return f"cp{ctypes.windll.kernel32.GetACP()}"

    def executable_file_filter(self) -> str:
        return "Executable files (*.exe)"
