# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

import pathlib
from collections.abc import Generator
from unittest import mock

import pytest
import pytestqt.qtbot
from PySide6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

import dill
import gremlin.device_initialization
import gremlin.event_handler
import gremlin.macro
import gremlin.sendinput
import gremlin.ui.backend
import gremlin.util
from gremlin import windows_event_hook
from gremlin.audio_player import AudioPlayer
from gremlin.tts import TTSManager
from test.application.fakes import (
    STICK,
    THROTTLE,
    KeyboardInjector,
    LogicalInjector,
    MouseInjector,
    Outputs,
    PhysicalInjector,
)
from test.application.ui_driver import UiDriver
from test.unit.conftest import make_fake_device
from vjoy import vjoy


@pytest.fixture(scope="session")
def stub_input_hooks() -> Generator[None]:
    """Keeps the user's real keys and mouse buttons out of the event listener."""
    with (
        mock.patch.object(windows_event_hook.KeyboardHook, "start"),
        mock.patch.object(windows_event_hook.MouseHook, "start"),
    ):
        yield


@pytest.fixture(scope="session")
def stub_update_check() -> Generator[None]:
    """Keeps the version check off the network."""
    with mock.patch.object(gremlin.util, "latest_gremlin_version", return_value=None):
        yield


@pytest.fixture(scope="session")
def qapp_args(
    pytestconfig: pytest.Config, stub_input_hooks: None, stub_update_check: None
) -> list[str]:
    """Configures the qapp fixture to run in offscreen mode."""
    return [pytestconfig.getini("qt_qapp_name"), "-platform", "offscreen"]


@pytest.fixture(scope="package", autouse=True)
def fake_devices(qapp: QtWidgets.QApplication) -> Generator[None]:
    """Exposes a fixed set of fake devices, one vJoy and two physical."""
    vjoy_device = make_fake_device(is_virtual=True)
    devices = [vjoy_device, STICK, THROTTLE]
    devices_by_uuid = {device.device_guid.uuid: device for device in devices}
    with (
        # Mock dill library functions to avoid dealing with real devices.
        mock.patch.object(dill.DILL, "input_event_handler", lambda *_: None),
        mock.patch.object(dill.DILL, "device_change_handler", lambda *_: None),
        mock.patch.object(dill.DILL, "get_device_count", return_value=len(devices)),
        mock.patch.object(
            dill.DILL,
            "get_device_information_by_index",
            side_effect=lambda index: devices[index],
        ),
        mock.patch.object(
            dill.DILL,
            "device_exists",
            side_effect=lambda guid: guid.uuid in devices_by_uuid,
        ),
        mock.patch.object(
            dill.DILL,
            "get_device_information_by_guid",
            side_effect=lambda guid: devices_by_uuid.get(
                guid.uuid, dill.DeviceSummary(dill._DeviceSummary())
            ),
        ),
        # Mock vJoy library functions to avoid dealing with vJoy.
        mock.patch.object(
            vjoy, "device_exists", side_effect=lambda vjoy_id: vjoy_id == 1
        ),
        mock.patch.object(vjoy, "axis_count", return_value=vjoy_device.axis_count),
        mock.patch.object(vjoy, "button_count", return_value=vjoy_device.button_count),
        mock.patch.object(vjoy, "hat_count", return_value=vjoy_device.hat_count),
        mock.patch.object(vjoy, "hat_configuration_valid", return_value=True),
    ):
        gremlin.device_initialization.joystick_devices_initialization()
        # Loads the calibration of the physical axes.
        gremlin.event_handler.EventListener()._init_joysticks()
        yield
    gremlin.device_initialization.joystick_devices_initialization()


@pytest.fixture(scope="package", autouse=True)
def package_outputs() -> Generator[Outputs]:
    """Mock several 'physical' outputs."""
    with (
        mock.patch.object(gremlin.macro, "send_key_down") as key_down,
        mock.patch.object(gremlin.macro, "send_key_up") as key_up,
        mock.patch.object(gremlin.sendinput, "_send_input") as send_input,
        mock.patch.multiple(
            AudioPlayer, start=mock.DEFAULT, stop=mock.DEFAULT, enqueue=mock.DEFAULT
        ) as audio,
        mock.patch.multiple(
            TTSManager, start=mock.DEFAULT, stop=mock.DEFAULT, enqueue=mock.DEFAULT
        ) as tts,
        mock.patch.object(QtCore.QProcess, "startDetached") as start_detached,
    ):
        outputs = Outputs(
            key_down=key_down,
            key_up=key_up,
            send_input=send_input,
            audio=audio,
            tts=tts,
            start_detached=start_detached,
        )
        with mock.patch.object(
            vjoy.VJoyProxy,
            "__getitem__",
            lambda _proxy, vjoy_id: outputs.vjoy[vjoy_id],
        ):
            yield outputs


@pytest.fixture
def outputs(package_outputs: Outputs) -> Outputs:
    package_outputs.reset()
    return package_outputs


@pytest.fixture
def backend() -> gremlin.ui.backend.Backend:
    return gremlin.ui.backend.Backend()


@pytest.fixture
def ui(
    qtbot: pytestqt.qtbot.QtBot, qapp: QtWidgets.QApplication
) -> Generator[UiDriver]:
    # qapp_args only applies when this folder creates the session's app.
    assert QtGui.QGuiApplication.platformName() == "offscreen", (
        "Run test/application in its own pytest session"
    )
    main_window = qapp.main_window
    main_window.showNormal()
    main_window.raise_()
    main_window.requestActivate()
    qtbot.waitExposed(main_window)
    # Ensure the main window is active as others key events don't reach it.
    qtbot.waitActive(main_window)
    driver = UiDriver(qtbot)
    yield driver
    # Ensure failures properly tear down everything.
    driver.reset(main_window)


@pytest.fixture
def empty_profile(
    backend: gremlin.ui.backend.Backend, tmp_path: pathlib.Path
) -> Generator[pathlib.Path]:
    """Starts from an empty profile that already has a file to save into."""
    path = tmp_path / "profile.xml"
    backend.newProfile()
    backend.saveProfile(str(path))
    yield path
    backend.newProfile()


@pytest.fixture
def inject_logical() -> LogicalInjector:
    return LogicalInjector()


@pytest.fixture
def inject_physical() -> PhysicalInjector:
    return PhysicalInjector()


@pytest.fixture
def inject_keyboard() -> KeyboardInjector:
    return KeyboardInjector()


@pytest.fixture
def inject_mouse() -> MouseInjector:
    return MouseInjector()
