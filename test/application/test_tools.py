# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import contextlib
import pathlib
from collections.abc import (
    Callable,
    Generator,
)

import pytest
from PySide6 import QtQuick

import dill
import gremlin.ui.backend
from action_plugins.description import DescriptionData
from action_plugins.map_to_vjoy import MapToVjoyData
from gremlin import (
    common,
    event_handler,
)
from gremlin.base_classes import AbstractActionData
from gremlin.config import Configuration
from gremlin.types import (
    AxisNames,
    InputType,
)
from test.application.fakes import (
    STICK,
    THROTTLE,
    PhysicalInjector,
)
from test.application.ui_driver import UiDriver
from test.application.ui_interaction import (
    add_description,
    add_mode,
    click_and_validate,
    find_action,
    find_description,
    open_dialog,
    save_and_reload,
    select_physical_input,
    set_spin_box_value,
)

_DEFAULT_CALIBRATION = [-32768, 0, 0, 32767, True]


def _inputs(device: dill.DeviceSummary) -> set[tuple[InputType, int]]:
    return (
        {
            (InputType.JoystickAxis, device.axis_map[linear_index].axis_index)
            for linear_index in range(device.axis_count)
        }
        | {
            (InputType.JoystickButton, button_id)
            for button_id in range(1, device.button_count + 1)
        }
        | {(InputType.JoystickHat, hat_id) for hat_id in range(1, device.hat_count + 1)}
    )


def _bound_actions(
    device: dill.DeviceSummary, mode: str = "Default"
) -> dict[tuple[InputType, int], list[AbstractActionData]]:
    """Returns the top-level actions of each of the device's bound inputs in mode."""
    profile = gremlin.ui.backend.Backend().profile
    return {
        (item.input_type, item.input_id): [
            action
            for binding in item.action_sequences
            for action in binding.root_action.get_actions()[0]
        ]
        for item in profile.inputs.get(device.device_guid.uuid, [])
        if item.mode == mode and item.action_sequences
    }


def _mapped_inputs(
    device: dill.DeviceSummary, mode: str = "Default"
) -> set[tuple[InputType, int]]:
    return {
        key
        for key, actions in _bound_actions(device, mode).items()
        if any(isinstance(action, MapToVjoyData) for action in actions)
    }


def _descriptions(device: dill.DeviceSummary) -> dict[tuple[InputType, int], list[str]]:
    return {
        key: [
            action.description
            for action in actions
            if isinstance(action, DescriptionData)
        ]
        for key, actions in _bound_actions(device).items()
    }


def test_input_viewer_lists_devices(ui: UiDriver) -> None:
    with open_dialog(ui, "Input Viewer", "inputViewerContent") as dialog:
        ui.wait_for_value(
            lambda: sorted(
                device.property("name")
                for device in ui.find_all("inputViewerDevice", dialog)
            ),
            sorted(["vJoy Device 1", STICK.name, THROTTLE.name]),
        )


@contextlib.contextmanager
def _auto_mapper(
    ui: UiDriver, devices: list[dill.DeviceSummary]
) -> Generator[QtQuick.QQuickItem]:
    """Opens the Auto Mapper with the physical devices and vJoy device 1 selected."""
    with open_dialog(ui, "Auto Mapper", "autoMapperContent") as dialog:
        for device in devices:
            _select_device(ui, dialog, "physicalDeviceCheckBox", device.name)
        _select_device(ui, dialog, "vjoyDeviceCheckBox", "vJoy Device 1")
        yield dialog


def _select_device(
    ui: UiDriver, dialog: QtQuick.QQuickItem, check_box_name: str, device_name: str
) -> None:
    check_box = ui.find_one_where(
        lambda item: (
            item.objectName() == check_box_name and item.property("text") == device_name
        ),
        f"selecting device '{device_name}'",
        dialog,
    )
    click_and_validate(ui, check_box)


def _create_mappings(ui: UiDriver, dialog: QtQuick.QQuickItem) -> None:
    status = ui.find_item("statusLabel", dialog)
    previous_status = status.property("text")
    ui.click(ui.find_item("createMappingsButton", dialog))
    ui.wait_until(lambda: status.property("text") != previous_status)


def test_auto_mapper_mode(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    add_mode(ui, "Second")
    with _auto_mapper(ui, [STICK]) as dialog:
        ui.select(ui.find_item("modeCombo", dialog), "Second")
        _create_mappings(ui, dialog)

    assert _mapped_inputs(STICK, "Second") == _inputs(STICK)
    assert _mapped_inputs(STICK) == set()
    assert _mapped_inputs(THROTTLE, "Second") == set()


def test_auto_mapper_overwrite(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    described_input = (InputType.JoystickButton, 1)
    select_physical_input(ui, STICK, *described_input)
    add_description(ui, "kept")
    with _auto_mapper(ui, [STICK]) as dialog:
        _create_mappings(ui, dialog)
        assert _mapped_inputs(STICK) == _inputs(STICK) - {described_input}

        # The selection must outlast a run.
        click_and_validate(ui, ui.find_item("overwriteCheckBox", dialog))
        _create_mappings(ui, dialog)
        assert _mapped_inputs(STICK) == _inputs(STICK)

    assert _descriptions(STICK)[described_input] == []
    find_action(ui, "Map to vJoy")
    ui.wait_until(lambda: not ui.find_all("actionNode_Description"))


def test_auto_mapper_repeat(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    with _auto_mapper(ui, [STICK, THROTTLE]) as dialog:
        click_and_validate(ui, ui.find_item("repeatCheckBox", dialog))
        _create_mappings(ui, dialog)

    # The stick takes both vJoy hats, so only repeating them maps the throttle's.
    assert _mapped_inputs(STICK) == _inputs(STICK)
    assert _mapped_inputs(THROTTLE) == _inputs(THROTTLE)


def test_swap_devices(ui: UiDriver, empty_profile: pathlib.Path) -> None:
    stick_input = (InputType.JoystickButton, 1)
    throttle_input = (InputType.JoystickButton, 2)
    select_physical_input(ui, STICK, *stick_input)
    add_description(ui, "stick")
    select_physical_input(ui, THROTTLE, *throttle_input)
    add_description(ui, "throttle")
    # Saving adds the devices' names to the profile, which the dialog lists.
    save_and_reload(ui, empty_profile)

    with open_dialog(ui, "Swap Devices", "swapDevicesContent") as dialog:
        ui.select(
            ui.find_item("profileDeviceCombo", dialog), f"{STICK.name} - 1 actions"
        )
        ui.select(ui.find_item("physicalDeviceCombo", dialog), THROTTLE.name)
        status = ui.find_item("statusLabel", dialog)
        ui.click(ui.find_item("swapBindingsButton", dialog))
        ui.wait_until(lambda: status.property("text").startswith("Swapped"))

    assert _descriptions(STICK) == {throttle_input: ["throttle"]}
    assert _descriptions(THROTTLE) == {stick_input: ["stick"]}

    save_and_reload(ui, empty_profile)
    select_physical_input(ui, THROTTLE, *stick_input)
    find_description(ui, "stick")
    select_physical_input(ui, STICK, *throttle_input)
    find_description(ui, "throttle")


@pytest.fixture
def restore_throttle_calibration() -> Generator[None]:
    yield
    config = Configuration()
    for linear_index in range(THROTTLE.axis_count):
        axis_index = THROTTLE.axis_map[linear_index].axis_index
        config.init_calibration(THROTTLE.device_guid.uuid, axis_index)
        config.set_calibration(
            THROTTLE.device_guid.uuid, axis_index, _DEFAULT_CALIBRATION
        )
        event_handler.EventListener().reload_calibration(
            THROTTLE.device_guid, axis_index
        )


@contextlib.contextmanager
def _calibrate_throttle(ui: UiDriver) -> Generator[QtQuick.QQuickItem]:
    """Opens the Calibration dialog showing the throttle's axes."""
    with open_dialog(ui, "Calibration", "calibrationContent") as dialog:
        ui.select(ui.find_item("deviceCombo", dialog), THROTTLE.name)
        # The stick's first two axes are named the same, its third is not.
        _axis_row(ui, dialog, 2)
        yield dialog


def _axis_row(
    ui: UiDriver, dialog: QtQuick.QQuickItem, linear_index: int
) -> QtQuick.QQuickItem:
    identifier = common.input_to_ui_string(
        InputType.JoystickAxis, THROTTLE.axis_map[linear_index].axis_index
    )
    return ui.find_one_where(
        lambda item: (
            item.objectName() == f"calibrationAxis_{linear_index}"
            and item.property("identifier") == identifier
        ),
        f"calibrating '{identifier}'",
        dialog,
    )


def _raw(value: float) -> int:
    return round(value * 32767)


def _stored_calibration(axis: AxisNames) -> list[int | bool]:
    return list(Configuration().get_calibration(THROTTLE.device_guid.uuid, axis.value))


def _record_calibration(
    ui: UiDriver, button: QtQuick.QQuickItem, inject: Callable[[], None]
) -> None:
    """Records the axis values inject produces with a calibrate button."""
    click_and_validate(ui, button)
    inject()
    click_and_validate(ui, button, False)


def test_calibration_live_input(
    ui: UiDriver,
    inject_physical: PhysicalInjector,
    restore_throttle_calibration: None,
) -> None:
    with _calibrate_throttle(ui) as dialog:
        # Wrappers found within a row die with the row's wrapper, so keep it.
        row = _axis_row(ui, dialog, 0)
        field = ui.find_item("rawValueField", row)
        inject_physical.axis(THROTTLE, AxisNames.X.value, 0.5)
        ui.wait_for_value(lambda: field.property("text"), str(_raw(0.5)))


def test_calibrate_extrema_and_center(
    ui: UiDriver,
    inject_physical: PhysicalInjector,
    restore_throttle_calibration: None,
) -> None:
    def inject(*values: float) -> Callable[[], None]:
        def emit() -> None:
            for value in values:
                inject_physical.axis(THROTTLE, AxisNames.X.value, value)

        return emit

    with _calibrate_throttle(ui) as dialog:
        row = _axis_row(ui, dialog, 0)
        _record_calibration(
            ui, ui.find_item("calibrateExtremaButton", row), inject(-0.8, 0.9)
        )
        _record_calibration(
            ui, ui.find_item("calibrateCenterButton", row), inject(-0.05, 0.04)
        )
        ui.click(ui.find_item("saveButton", row))
        expected = [_raw(-0.8), _raw(-0.05), _raw(0.04), _raw(0.9), True]
        ui.wait_for_value(lambda: _stored_calibration(AxisNames.X), expected)


def test_calibration_manual_values(
    ui: UiDriver, restore_throttle_calibration: None
) -> None:
    with _calibrate_throttle(ui) as dialog:
        row = _axis_row(ui, dialog, 1)
        click_and_validate(ui, ui.find_item("withCenterCheckBox", row), False)
        set_spin_box_value(ui, ui.find_item("lowSpinBox", row), -30000)
        set_spin_box_value(ui, ui.find_item("highSpinBox", row), 30000)
        ui.click(ui.find_item("saveButton", row))
        ui.wait_for_value(
            lambda: _stored_calibration(AxisNames.Y), [-30000, 0, 0, 30000, False]
        )

        ui.click(ui.find_item("resetButton", row))
        ui.click(ui.find_item("saveButton", row))
        ui.wait_for_value(
            lambda: _stored_calibration(AxisNames.Y), [-32768, 0, 0, 32767, False]
        )
