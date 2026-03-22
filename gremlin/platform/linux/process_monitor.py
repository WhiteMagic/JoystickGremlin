# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Linux process-detection backend — /proc + Wayland compositor APIs.

Supported compositors (auto-detected at startup):
  - Sway     : SWAYSOCK env var → swaymsg -t get_tree
  - Hyprland : HYPRLAND_INSTANCE_SIGNATURE env var → hyprctl activewindow -j
  - GNOME    : XDG_CURRENT_DESKTOP contains "gnome" + WAYLAND_DISPLAY → gdbus

All methods fall back gracefully when the compositor is unknown or when
the relevant helper binary is absent.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess

from gremlin.platform.base import AbstractProcessBackend

_log = logging.getLogger("system")


class ProcessBackend(AbstractProcessBackend):

    """Linux implementation using /proc and Wayland compositor D-Bus / IPC."""

    _SUBPROCESS_TIMEOUT = 0.5  # seconds

    def __init__(self) -> None:
        self._cached_pid: int = -1
        self._cached_path: str = ""
        self._compositor: str | None = self._detect_compositor()
        if self._compositor:
            _log.debug("ProcessBackend: detected compositor '%s'", self._compositor)
        else:
            _log.debug("ProcessBackend: no supported compositor detected")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_active_process_path(self) -> str | None:
        """Return the executable path of the currently focused window's process."""
        if self._compositor is None:
            return None
        pid = self._active_pid()
        if pid is None:
            return None
        if pid == self._cached_pid:
            return self._cached_path or None
        self._cached_pid = pid
        path = self._pid_to_path(pid)
        self._cached_path = path or ""
        return path

    def list_process_paths(self) -> list[str]:
        """Return a sorted, deduplicated list of all running executable paths."""
        paths: set[str] = set()
        try:
            for entry in os.scandir("/proc"):
                if not entry.name.isdigit():
                    continue
                try:
                    exe = os.readlink(f"/proc/{entry.name}/exe")
                    if exe:
                        paths.add(exe)
                except OSError:
                    pass
        except OSError as exc:
            _log.debug("ProcessBackend: cannot scan /proc: %s", exc)
        return sorted(paths)

    # ------------------------------------------------------------------
    # Compositor detection
    # ------------------------------------------------------------------

    def _detect_compositor(self) -> str | None:
        if os.environ.get("SWAYSOCK"):
            return "sway"
        if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
            return "hyprland"
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "gnome" in desktop and os.environ.get("WAYLAND_DISPLAY"):
            return "gnome"
        return None

    # ------------------------------------------------------------------
    # Active PID helpers
    # ------------------------------------------------------------------

    def _active_pid(self) -> int | None:
        if self._compositor == "sway":
            return self._sway_active_pid()
        if self._compositor == "hyprland":
            return self._hyprland_active_pid()
        if self._compositor == "gnome":
            return self._gnome_active_pid()
        return None

    def _sway_active_pid(self) -> int | None:
        out = self._run(["swaymsg", "-t", "get_tree"])
        if out is None:
            return None
        try:
            return self._sway_find_focused(json.loads(out))
        except Exception:
            return None

    def _sway_find_focused(self, node: dict) -> int | None:
        """Recursively find the focused node and return its PID."""
        if node.get("focused") and node.get("pid"):
            return int(node["pid"])
        for child in node.get("nodes", []) + node.get("floating_nodes", []):
            result = self._sway_find_focused(child)
            if result is not None:
                return result
        return None

    def _hyprland_active_pid(self) -> int | None:
        out = self._run(["hyprctl", "activewindow", "-j"])
        if out is None:
            return None
        try:
            data = json.loads(out)
            pid = data.get("pid")
            return int(pid) if pid else None
        except Exception:
            return None

    def _gnome_active_pid(self) -> int | None:
        # GNOME Shell exposes a JS eval endpoint via D-Bus.
        out = self._run([
            "gdbus", "call", "--session",
            "--dest", "org.gnome.Shell",
            "--object-path", "/org/gnome/Shell",
            "--method", "org.gnome.Shell.Eval",
            "global.display.focus_window?.get_pid() ?? -1",
        ])
        if out is None:
            return None
        try:
            # Response format: (true, '"12345"')
            import re
            m = re.search(r"(\d+)", out)
            if m:
                pid = int(m.group(1))
                return pid if pid > 0 else None
        except Exception:
            pass
        return None

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _pid_to_path(self, pid: int) -> str | None:
        try:
            return os.readlink(f"/proc/{pid}/exe")
        except OSError:
            return None

    def _run(self, cmd: list[str]) -> str | None:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._SUBPROCESS_TIMEOUT,
            )
            return result.stdout if result.returncode == 0 else None
        except Exception as exc:
            _log.debug("ProcessBackend: %s failed: %s", cmd[0], exc)
            return None
