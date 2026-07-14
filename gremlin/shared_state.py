# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gremlin import profile


"""Stores global state that needs to be shared between various
parts of the program.

This is ugly but the only sane way to do this at the moment.
"""

# Flag indicating whether or not input highlighting should be
# prevented even if it is enabled by the user
_suspend_input_highlighting = False

# Timer used to disable input highlighting with a delay
_suspend_timer = None

# Holds the currently active profile
current_profile: None | profile.Profile = None


def suspend_input_highlighting() -> bool:
    """Returns whether or not input highlighting is suspended.

    :return True if input's are not automatically selected, False otherwise
    """
    return _suspend_input_highlighting


def set_suspend_input_highlighting(value: bool) -> None:
    """Sets the input highlighting behavior.

    Args:
        value: if True disables automatic selection of used inputs, if False
            inputs will automatically be selected upon use
    """
    global _suspend_input_highlighting, _suspend_timer
    if _suspend_timer is not None:
        _suspend_timer.cancel()
    _suspend_input_highlighting = value


def set_suspend_input_highlighting_delayed() -> None:
    """Disables input highlighting with a delay."""
    global _suspend_timer
    if _suspend_timer is not None:
        _suspend_timer.cancel()

    _suspend_timer = threading.Timer(2, lambda: set_suspend_input_highlighting(False))
    _suspend_timer.start()
