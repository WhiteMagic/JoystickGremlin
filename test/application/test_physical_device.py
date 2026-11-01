# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib

from gremlin.types import (
    AxisNames,
    InputType,
)
from test.application.fakes import (
    STICK,
    THROTTLE,
)
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_description,
    find_description,
    save_and_reload,
    select_physical_input,
)


def test_bindings_per_device(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    # The slider is the throttle's fourth axis, but has axis index 7.
    descriptions = [
        (STICK, InputType.JoystickButton, 1, "stick button"),
        (THROTTLE, InputType.JoystickAxis, AxisNames.SLIDER.value, "throttle slider"),
    ]
    for device, input_type, input_id, text in descriptions:
        select_physical_input(ui, device, input_type, input_id)
        add_description(ui, text)

    save_and_reload(ui, empty_profile)
    # Each selection switches the device, so the shown binding is a reloaded one.
    for device, input_type, input_id, text in descriptions:
        select_physical_input(ui, device, input_type, input_id)
        find_description(ui, text)
