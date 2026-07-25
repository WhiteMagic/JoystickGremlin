# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import sys

sys.path.append(".")

import importlib
import inspect
from pathlib import Path

import gremlin.util

_ACTION_PLUGINS_DIR = Path(gremlin.util.resource_path("action_plugins"))

# RootAction is intentionally invisible (qml/InputItemBinding.qml never draws its own
# row) and ships no icon of its own.
_NO_ICON_EXPECTED = {"root"}


def _plugin_dirs() -> list[str]:
    return sorted(p.parent.name for p in _ACTION_PLUGINS_DIR.glob("*/__init__.py"))


def test_every_plugin_module_resolves_to_its_own_directory() -> None:
    """Guards the assumption `ActionModel._icon_path_impl` relies on: a plugin's data
    class is always defined in that plugin's own folder, so `inspect.getfile` resolves
    correctly without any tag/directory naming convention."""
    for plugin_dir in _plugin_dirs():
        module = importlib.import_module(f"action_plugins.{plugin_dir}")
        if "create" not in module.__dict__:
            continue
        module_file = Path(inspect.getfile(module.create))
        assert module_file.parent.name == plugin_dir


def test_every_plugin_ships_an_icon_except_root() -> None:
    for plugin_dir in _plugin_dirs():
        if plugin_dir in _NO_ICON_EXPECTED:
            continue
        module = importlib.import_module(f"action_plugins.{plugin_dir}")
        if "create" not in module.__dict__:
            continue
        own_icon = Path(inspect.getfile(module.create)).parent / "icon.svg"
        assert own_icon.exists(), f"{plugin_dir} has no icon.svg next to its module"
        assert "currentColor" in own_icon.read_text(encoding="utf-8"), (
            f"{plugin_dir}/icon.svg must use currentColor to tint via IconProvider"
        )


def test_action_placeholder_exists_and_is_tintable() -> None:
    placeholder = _ACTION_PLUGINS_DIR / "action-placeholder.svg"
    assert placeholder.exists()
    assert "currentColor" in placeholder.read_text(encoding="utf-8")
