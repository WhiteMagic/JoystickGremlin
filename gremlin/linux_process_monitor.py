# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2025 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Linux-native process monitoring using psutil.

Replaces the Windows-specific process_monitor.py that used win32gui/win32process.
"""

import logging
import os
import time
import threading
from typing import List, Optional

from PySide6 import QtCore

try:
    import psutil
except ImportError:
    psutil = None  # type: ignore
    logging.warning("psutil not available - process monitoring disabled")

# Try to get active window information (X11/Wayland)
try:
    from ewmh import EWMH
    _ewmh = EWMH()
    _has_ewmh = True
except ImportError:
    _ewmh = None
    _has_ewmh = False
    logging.info("python-ewmh not available - active window detection limited")


class ProcessMonitor(QtCore.QObject):

    """Monitors the currently active window process on Linux.

    This class continuously monitors the active window and whenever
    it changes the path to the executable is retrieved and signaled
    to the rest of the system using Qt's signal / slot mechanism.
    
    Uses psutil for cross-platform process information and EWMH
    (Extended Window Manager Hints) for X11 window manager integration.
    """

    # Signal emitted when the active window changes
    process_changed = QtCore.Signal(str)

    def __init__(self):
        """Creates a new instance."""
        QtCore.QObject.__init__(self)
        self._logger = logging.getLogger("system")
        self._current_path = ""
        self._current_pid = -1
        self.running = False
        self._update_thread = None
        
        # Check if psutil is available
        if psutil is None:
            self._logger.warning(
                "psutil not installed - process monitoring unavailable. "
                "Install with: pip install psutil"
            )

    def start(self):
        """Starts monitoring the current process."""
        if not self.running and psutil is not None:
            self.running = True
            self._update_thread = threading.Thread(
                target=self._update,
                daemon=True
            )
            self._update_thread.start()
            self._logger.info("Process monitor started")

    def stop(self):
        """Stops monitoring the current process."""
        self.running = False
        if self._update_thread is not None:
            self._update_thread.join(timeout=2.0)
            self._logger.info("Process monitor stopped")

    def _get_active_window_pid(self) -> Optional[int]:
        """Get the PID of the currently active window.
        
        Returns:
            PID of active window or None if unavailable
        """
        if _has_ewmh and _ewmh is not None:
            try:
                active_window = _ewmh.getActiveWindow()
                if active_window is not None:
                    pid = _ewmh.getWmPid(active_window)
                    return pid
            except Exception as e:
                self._logger.debug(f"EWMH active window detection failed: {e}")
        
        # Fallback: Use /proc to find X server and get focused window
        # This is less reliable but works without python-ewmh
        try:
            # Alternative: Parse xdotool or wmctrl output
            import subprocess
            result = subprocess.run(
                ['xdotool', 'getactivewindow', 'getwindowpid'],
                capture_output=True,
                text=True,
                timeout=1.0
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass
        
        return None

    def _get_process_executable(self, pid: int) -> Optional[str]:
        """Get the executable path for a given PID.
        
        Args:
            pid: Process ID
            
        Returns:
            Full path to executable or None if unavailable
        """
        try:
            process = psutil.Process(pid)
            exe_path = process.exe()
            return os.path.normpath(exe_path)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            self._logger.debug(f"Could not get executable for PID {pid}: {e}")
            return None

    def _update(self):
        """Monitors the active process for changes."""
        while self.running:
            try:
                pid = self._get_active_window_pid()
                
                if pid is not None and pid != self._current_pid:
                    self._current_pid = pid
                    exe_path = self._get_process_executable(pid)
                    
                    if exe_path is not None and exe_path != self._current_path:
                        self._current_path = exe_path
                        self._logger.debug(f"Active process changed to: {exe_path}")
                        self.process_changed.emit(self.current_path)
                
            except Exception as e:
                self._logger.error(f"Error in process monitor update: {e}")
            
            time.sleep(1.0)

    @property
    def current_path(self) -> str:
        """Returns the path to the currently active executable.

        Returns:
            Path to the currently active executable
        """
        return self._current_path


def list_current_processes() -> List[str]:
    """Returns a list of executable paths to currently active processes.

    Returns:
        List of active process executable paths
    """
    if psutil is None:
        logging.warning("psutil not available - cannot list processes")
        return []
    
    process_list = []
    
    try:
        for proc in psutil.process_iter(['exe', 'name']):
            try:
                exe_path = proc.info['exe']
                if exe_path is not None:
                    process_list.append(os.path.normpath(exe_path))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception as e:
        logging.error(f"Error listing processes: {e}")
    
    return sorted(set(process_list))
