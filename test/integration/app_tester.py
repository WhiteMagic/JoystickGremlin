# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import time
import uuid
from typing import (
    Callable,
    TypeVar,
)

import pytest
from PySide6 import QtWidgets

import dill
import gremlin.input_cache
import gremlin.types
from action_plugins import map_to_logical_device
from gremlin import (
    base_classes,
    event_handler,
    logical_device,
    mode_manager,
)

_InputTypeT = TypeVar("_InputTypeT")

_ASSERT_EVENTUALLY_MAX_DELAY = 1  # Seconds
_ASSERT_EVENTUALLY_RETRY_DELAY = 0.01  # Seconds

# The max delta below for integration testing is determined by the following factors:
# 1. vJoy range is 0-32767, but DirectInput default axis range is 0-65535.
# 2. The "calibration" of axis values for Dill reads is done on a different range than
#    the uncalibration of axis values for vJoy. Specifically, the ratio of points on
#    either side of zero is different.
# 3. We loop-back the device, potentially doubling the above errors.
_INTEGER_AXIS_MAX_DELTA = 4
_FLOAT_AXIS_MAX_DELTA = 7 / 65536


class GremlinAppTester:
    """Helper class for assertions in integration tests."""

    AXIS_MAX_INT = 32767

    def __init__(self, app: QtWidgets.QApplication) -> None:
        self.app = app

    def inject_logical_input(
        self,
        logical_action: map_to_logical_device.MapToLogicalDeviceData,
        value: float | bool | gremlin.types.HatDirection,
    ) -> None:
        functor = map_to_logical_device.MapToLogicalDeviceFunctor(logical_action)
        # Not used today, but let's create a valid one anyway.
        event = event_handler.Event(
            event_type=logical_action.logical_input_type,
            identifier=logical_action.logical_input_id,
            device_guid=dill.UUID_LogicalDevice,
            mode=mode_manager.ModeManager().current.name,
            value=value,
        )
        functor(event, base_classes.Value(value))

    def _assert_input_eventually_equals(
        self,
        fresh_input_cb: Callable[[], _InputTypeT],
        expected: _InputTypeT,
        min_delay: float = 0,
        max_delay: float = _ASSERT_EVENTUALLY_MAX_DELAY,
    ) -> None:
        start_t = time.monotonic()
        last_exception = None
        while time.monotonic() - start_t < max_delay:
            try:
                self.app.processEvents()
                assert fresh_input_cb() == expected
            except AssertionError as e:
                last_exception = e
                time.sleep(_ASSERT_EVENTUALLY_RETRY_DELAY)
            else:
                assert time.monotonic() - start_t >= min_delay
                return
        else:
            if last_exception is not None:
                raise last_exception

    # Assertions on input cache values.

    def assert_cached_axis_eventually_equals(
        self,
        device_uuid: uuid.UUID,
        axis_id: int,
        expected: float,
        min_delay: float = 0,
        max_delay: float = _ASSERT_EVENTUALLY_MAX_DELAY,
    ) -> None:
        try:
            joystick_cache = gremlin.input_cache.Joystick()[device_uuid]
        except gremlin.error.GremlinError as e:
            raise AssertionError("Could not validate cached axis") from e
        self._assert_input_eventually_equals(
            lambda: joystick_cache.axis(axis_id).value,
            pytest.approx(expected, abs=_FLOAT_AXIS_MAX_DELTA),
            min_delay,
            max_delay,
        )

    def assert_cached_button_eventually_equals(
        self,
        device_uuid: uuid.UUID,
        button_id: int,
        expected: bool,
        min_delay: float = 0,
        max_delay: float = _ASSERT_EVENTUALLY_MAX_DELAY,
    ) -> None:
        try:
            joystick_cache = gremlin.input_cache.Joystick()[device_uuid]
        except gremlin.error.GremlinError as e:
            raise AssertionError("Could not validate cached button") from e
        self._assert_input_eventually_equals(
            lambda: joystick_cache.button(button_id).is_pressed,
            expected,
            min_delay,
            max_delay,
        )

    def assert_cached_hat_eventually_equals(
        self,
        device_uuid: uuid.UUID,
        hat_id: int,
        expected: gremlin.types.HatDirection,
        min_delay: float = 0,
        max_delay: float = _ASSERT_EVENTUALLY_MAX_DELAY,
    ) -> None:
        try:
            joystick_cache = gremlin.input_cache.Joystick()[device_uuid]
        except gremlin.error.GremlinError as e:
            raise AssertionError("Could not validate cached hat") from e
        self._assert_input_eventually_equals(
            lambda: joystick_cache.hat(hat_id).direction,
            expected,
            min_delay,
            max_delay,
        )

    # Assertions on DirectInput readings.

    def assert_axis_eventually_equals(
        self,
        di_device_guid: dill.GUID,
        axis_id: int,
        expected: int,
        min_delay: float = 0,
        max_delay: float = _ASSERT_EVENTUALLY_MAX_DELAY,
    ) -> None:
        self._assert_input_eventually_equals(
            lambda: dill.DILL.get_axis(di_device_guid, axis_id),
            pytest.approx(expected, abs=_INTEGER_AXIS_MAX_DELTA),
            min_delay,
            max_delay,
        )

    def assert_button_eventually_equals(
        self,
        di_device_guid: dill.GUID,
        button_id: int,
        expected: bool,
        min_delay: float = 0,
        max_delay: float = _ASSERT_EVENTUALLY_MAX_DELAY,
    ) -> None:
        self._assert_input_eventually_equals(
            lambda: dill.DILL.get_button(di_device_guid, button_id),
            expected,
            min_delay,
            max_delay,
        )

    def assert_hat_eventually_equals(
        self,
        di_device_guid: dill.GUID,
        hat_id: int,
        expected: int,
        min_delay: float = 0,
        max_delay: float = _ASSERT_EVENTUALLY_MAX_DELAY,
    ) -> None:
        self._assert_input_eventually_equals(
            lambda: dill.DILL.get_hat(di_device_guid, hat_id),
            expected,
            min_delay,
            max_delay,
        )

    def assert_logical_axis_eventually_equals(
        self,
        axis_id: int,
        expected: int,
        min_delay: float = 0,
        max_delay: float = _ASSERT_EVENTUALLY_MAX_DELAY,
    ) -> None:
        self._assert_input_eventually_equals(
            lambda: (
                gremlin.input_cache.Joystick()[dill.GUID_LogicalDevice.uuid][
                    logical_device.LogicalDevice.Input.Identifier(
                        gremlin.types.InputType.JoystickAxis, axis_id
                    )
                ].value
            ),
            pytest.approx(expected, abs=_FLOAT_AXIS_MAX_DELTA),
            min_delay,
            max_delay,
        )
