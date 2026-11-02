# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import logging
import uuid
from collections.abc import (
    Callable,
    Generator,
)
from types import SimpleNamespace
from unittest import mock

import pytest

from gremlin import (
    code_runner,
    device_initialization,
    error,
    input_cache,
    input_refresh,
    mode_manager,
    shared_state,
)
from gremlin.config import Configuration
from gremlin.profile import Profile


def _mock_vjoy_proxy(
    monkeypatch: pytest.MonkeyPatch, vjoy_ids: tuple[int, ...]
) -> dict[int, mock.MagicMock]:
    devices = {vjoy_id: mock.MagicMock() for vjoy_id in vjoy_ids}

    def lookup(vjoy_id: int) -> mock.MagicMock:
        if vjoy_id not in devices:
            raise error.VJoyError(f"vJoy {vjoy_id} is not available")
        return devices[vjoy_id]

    proxy = mock.MagicMock()
    proxy.__getitem__.side_effect = lookup
    monkeypatch.setattr(code_runner, "VJoyProxy", lambda: proxy)
    return devices


@pytest.fixture
def runner() -> code_runner.CodeRunner:
    instance = code_runner.CodeRunner()
    instance._profile = Profile()
    return instance


@pytest.fixture
def set_refresh_on_activation() -> Generator[Callable[[bool], None]]:
    configuration = Configuration()
    option = ("global", "behavior", "refresh-axis-on-activation")
    original_value = configuration.value(*option)

    yield lambda enabled: configuration.set(*option, enabled)

    configuration.set(*option, original_value)


@pytest.fixture
def activation_calls(
    monkeypatch: pytest.MonkeyPatch, runner: code_runner.CodeRunner
) -> Generator[list[str]]:
    """Records the activation steps whose order matters and stops the runner."""
    calls: list[str] = []
    manager = mode_manager.ModeManager()
    monkeypatch.setattr(manager, "_mode_stack", [mode_manager.Mode("Default", None)])
    monkeypatch.setattr(shared_state, "current_profile", None)
    monkeypatch.setattr(
        input_refresh.RefreshPhysicalInputs,
        "refresh_axes",
        lambda: calls.append("refresh_axes"),
    )
    monkeypatch.setattr(
        runner, "_apply_vjoy_initial_values", lambda: calls.append("initial_values")
    )
    monkeypatch.setattr(runner.event_handler, "resume", lambda: calls.append("resume"))
    mouse_motion = mock.MagicMock()
    mouse_motion.start.side_effect = lambda: calls.append("mouse_motion_start")
    monkeypatch.setattr(
        code_runner.sendinput, "MouseMotionManager", lambda: mouse_motion
    )
    # Would create a real speech engine that outlives the test.
    monkeypatch.setattr(code_runner.tts, "TTSManager", mock.MagicMock())

    yield calls

    runner.stop()


def test_initial_value_uses_axis_index_on_device_with_axis_gaps(
    monkeypatch: pytest.MonkeyPatch, runner: code_runner.CodeRunner
) -> None:
    devices = _mock_vjoy_proxy(monkeypatch, (1,))
    # Axis index 8 is linear index 6 on the conftest device.
    runner._profile.settings.set_initial_vjoy_axis_value(vid=1, aid=8, value=0.5)

    runner._apply_vjoy_initial_values()

    devices[1].axis.assert_called_once_with(axis_id=8)
    assert devices[1].axis.return_value.value == 0.5


def test_initial_value_on_higher_vjoy_id_is_applied(
    monkeypatch: pytest.MonkeyPatch, runner: code_runner.CodeRunner
) -> None:
    devices = _mock_vjoy_proxy(monkeypatch, (1, 2))
    real_device = device_initialization.vjoy_devices()[0]
    second_device = SimpleNamespace(
        vjoy_id=2, device_guid=real_device.device_guid, axis_map=real_device.axis_map
    )
    monkeypatch.setattr(
        device_initialization, "vjoy_devices", lambda: [real_device, second_device]
    )
    runner._profile.settings.set_initial_vjoy_axis_value(vid=2, aid=1, value=0.5)

    runner._apply_vjoy_initial_values()

    devices[1].axis.assert_not_called()
    devices[2].axis.assert_called_once_with(axis_id=1)
    assert devices[2].axis.return_value.value == 0.5


def test_failed_snapshot_only_skips_the_affected_device(
    monkeypatch: pytest.MonkeyPatch, runner: code_runner.CodeRunner
) -> None:
    devices = _mock_vjoy_proxy(monkeypatch, (1, 2))
    real_device = device_initialization.vjoy_devices()[0]
    unknown_device = SimpleNamespace(
        vjoy_id=1,
        device_guid=SimpleNamespace(uuid=uuid.uuid4()),
        axis_map=real_device.axis_map,
    )
    second_device = SimpleNamespace(
        vjoy_id=2, device_guid=real_device.device_guid, axis_map=real_device.axis_map
    )
    monkeypatch.setattr(
        device_initialization, "vjoy_devices", lambda: [unknown_device, second_device]
    )
    runner._profile.settings.set_initial_vjoy_axis_value(vid=1, aid=1, value=0.25)
    runner._profile.settings.set_initial_vjoy_axis_value(vid=2, aid=1, value=0.5)

    runner._apply_vjoy_initial_values()

    devices[1].axis.assert_not_called()
    devices[2].axis.assert_called_once_with(axis_id=1)
    assert devices[2].axis.return_value.value == 0.5


def test_missing_vjoy_device_logs_warning_and_applies_remaining_values(
    monkeypatch: pytest.MonkeyPatch,
    runner: code_runner.CodeRunner,
    caplog: pytest.LogCaptureFixture,
) -> None:
    devices = _mock_vjoy_proxy(monkeypatch, (1,))
    runner._profile.settings.set_initial_vjoy_axis_value(vid=3, aid=1, value=0.25)
    runner._profile.settings.set_initial_vjoy_axis_value(vid=1, aid=1, value=0.5)

    with caplog.at_level(logging.WARNING, logger="system"):
        runner._apply_vjoy_initial_values()

    devices[1].axis.assert_called_once_with(axis_id=1)
    assert devices[1].axis.return_value.value == 0.5
    assert "vJoy 3" in caplog.text


def test_axis_with_non_zero_snapshot_keeps_its_value(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
    runner: code_runner.CodeRunner,
) -> None:
    devices = _mock_vjoy_proxy(monkeypatch, (1,))
    real_device = device_initialization.vjoy_devices()[0]
    cached_axis = input_cache.Joystick()[real_device.device_guid.uuid].axis(1)
    cached_axis.update(0.75)
    request.addfinalizer(lambda: cached_axis.update(0.0))
    runner._profile.settings.set_initial_vjoy_axis_value(vid=1, aid=1, value=0.5)

    runner._apply_vjoy_initial_values()

    devices[1].axis.assert_not_called()


def test_activation_order_mouse_motion_resume_initial_values_then_single_refresh(
    runner: code_runner.CodeRunner,
    activation_calls: list[str],
    set_refresh_on_activation: Callable[[bool], None],
) -> None:
    set_refresh_on_activation(True)

    runner.start(Profile())

    assert activation_calls == [
        "mouse_motion_start",
        "resume",
        "initial_values",
        "refresh_axes",
    ]


def test_activation_skips_axis_refresh_when_option_is_off(
    runner: code_runner.CodeRunner,
    activation_calls: list[str],
    set_refresh_on_activation: Callable[[bool], None],
) -> None:
    set_refresh_on_activation(False)

    runner.start(Profile())

    assert "initial_values" in activation_calls
    assert "refresh_axes" not in activation_calls


def test_mode_change_refreshes_axes_when_activation_option_is_off(
    runner: code_runner.CodeRunner,
    activation_calls: list[str],
    set_refresh_on_activation: Callable[[bool], None],
) -> None:
    set_refresh_on_activation(False)
    runner.start(Profile())
    activation_calls.clear()

    mode_manager.ModeManager().switch_to(mode_manager.Mode("Other", "Default"))

    assert activation_calls == ["refresh_axes"]
