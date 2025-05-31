# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2024 Lionel Ott
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

import time
from typing import Callable, TypeVar
import uuid

import pytest
from PySide6 import QtWidgets

import dill
import gremlin.input_cache
import gremlin.types

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

    def __init__(self, app: QtWidgets.QApplication):
        self.app = app

    def _assert_input_eventually_equals(
        self,
        fresh_input_cb: Callable[[], _InputTypeT],
        expected: _InputTypeT,
        min_delay: float = 0,
        max_delay: float = _ASSERT_EVENTUALLY_MAX_DELAY,
    ):
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
    ):
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
    ):
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
    ):
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
    ):
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
    ):
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
    ):
        self._assert_input_eventually_equals(
            lambda: dill.DILL.get_hat(di_device_guid, hat_id),
            expected,
            min_delay,
            max_delay,
        )
