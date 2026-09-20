# SPDX-License-Identifier: GPL-3.0-only

import gremlin.config
import gremlin.util
from gremlin.types import PropertyType


def register_config_options() -> None:
    _register_internal()
    _register_global()
    _register_appearance()
    _register_behavior()
    _register_action()
    _register_profile()


def _register_internal() -> None:
    cfg = gremlin.config.Configuration()
    cfg.register(
        "global",
        "internal",
        "last-mode",
        PropertyType.String,
        "Default",
        "Name of the last active mode",
        {},
    )
    cfg.register(
        "global",
        "internal",
        "last-profile",
        PropertyType.String,
        "",
        "Most recently used profile",
        {},
    )
    cfg.register(
        "global",
        "internal",
        "recent-profiles",
        PropertyType.List,
        [],
        "List of recently opened profiles",
        {},
    )
    cfg.register(
        "global",
        "internal",
        "last-known-version",
        PropertyType.String,
        gremlin.util.get_code_version(),
        "Last known version of Gremlin.",
        {},
    )
    cfg.register(
        "global",
        "internal",
        "main-window-geometry",
        PropertyType.List,
        [],
        "Persisted position and size of the main window.",
        {},
        False,
    )
    cfg.register(
        "global",
        "internal",
        "input-viewer-geometry",
        PropertyType.List,
        [],
        "Persisted position and size of the Input Viewer window.",
        {},
        False,
    )


def _register_global() -> None:
    cfg = gremlin.config.Configuration()
    cfg.register(
        "global",
        "general",
        "check-for-updates",
        PropertyType.Bool,
        True,
        "Check for new Gremlin versions online upon start.",
        {},
        True,
    )
    cfg.register(
        "global",
        "general",
        "plugin-directory",
        PropertyType.Path,
        "",
        "Directory containing additional action plugins",
        {"is_folder": True},
        True,
    )


def _register_appearance() -> None:
    cfg = gremlin.config.Configuration()
    cfg.register(
        "global",
        "appearance",
        "ui-scale",
        PropertyType.Selection,
        "100",
        "UI scaling percentage.",
        {"valid_options": ["100", "150", "200"]},
        True,
    )
    cfg.register(
        "global",
        "appearance",
        "theme",
        PropertyType.String,
        "light",
        "Currently used color theme for the UI.",
        {},
        False,
    )
    cfg.register(
        "global",
        "appearance",
        "display-mode",
        PropertyType.Selection,
        "Numerical and Label",
        "Defines how input name is displayed.",
        {"valid_options": ["Numerical", "Numerical and Label", "Label"]},
        True,
    )
    cfg.register(
        "global",
        "appearance",
        "action-sequence-visualization",
        PropertyType.Selection,
        "Chips",
        "Defines how action sequences associated with inputs are displayed.",
        {"valid_options": ["Chips", "Count"]},
        True,
    )


def _register_behavior() -> None:
    cfg = gremlin.config.Configuration()
    cfg.register(
        "global",
        "behavior",
        "device-change-behavior",
        PropertyType.Selection,
        "Reload",
        "Action Gremlin takes when a joystick is connected or disconnected.",
        {"valid_options": ["Disable", "Ignore", "Reload"]},
        True,
    )
    cfg.register(
        "global",
        "behavior",
        "minimize-to-tray",
        PropertyType.Bool,
        False,
        "Minimize the Gremlin window to the system tray instead of the taskbar.",
        {},
        True,
    )
    cfg.register(
        "global",
        "behavior",
        "close-to-tray",
        PropertyType.Bool,
        False,
        "Closing the Gremlin window hides it in the system tray rather than "
        "terminating Gremlin. Quit via the tray icon's menu.",
        {},
        True,
    )
    cfg.register(
        "global",
        "behavior",
        "refresh-axis-on-activation",
        PropertyType.Bool,
        True,
        "Use known physical device state to perform actions using these values "
        "upon profile activation.",
        {},
        True,
    )
    cfg.register(
        "global",
        "behavior",
        "refresh-axis-on-mode-change",
        PropertyType.Bool,
        True,
        "Force an update of all axes by emitting axis events upon a mode change.",
        {},
        True,
    )
    cfg.register(
        "global",
        "behavior",
        "input-highlighting",
        PropertyType.Bool,
        True,
        "Select the input in the UI by using an input on the physical device. "
        "Selects only inputs if the active tab matches the device.",
        {},
        True,
    )


def _register_action() -> None:
    cfg = gremlin.config.Configuration()
    cfg.register(
        "action",
        "action-priorities",
        "action-priorities",
        PropertyType.List,
        [],
        "Priority order of the actions",
        {},
        True,
    )
    cfg.register(
        "action",
        "map-to-mouse",
        "update-rate",
        PropertyType.Int,
        100,
        "Rate in Hz at which mouse motion updates are sent. Higher values give "
        "smoother motion at high speeds at the cost of additional CPU usage.",
        {"min": 50, "max": 500},
        True,
    )


def _register_profile() -> None:
    cfg = gremlin.config.Configuration()
    cfg.register(
        "profile",
        "automation",
        "enable-auto-loading",
        PropertyType.Bool,
        False,
        "Enable the automatic loading and activation of profiles based on the "
        "specified executable and profile combinations.",
        {},
        True,
    )
    cfg.register(
        "profile",
        "automation",
        "remain-active-on-focus-loss",
        PropertyType.Bool,
        False,
        "Keep the profile active when the monitored executable loses focus and "
        "the newly focused executable does not have a profile assigned to it.",
        {},
        True,
    )
    cfg.register(
        "profile",
        "automation",
        "entries-auto-loading",
        PropertyType.List,
        [],
        "List of executable and profile combinations for automatic loading.",
        {},
        False,
    )
