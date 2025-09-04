import sys
import uuid
sys.path.append(".")

import pathlib
from unittest import mock

import dill
import pytest
from vjoy import vjoy

# Import creates required user profile directory.
import joystick_gremlin
import gremlin.device_initialization
import gremlin.event_handler


def get_fake_device_guid(is_virtual: bool) -> dill._GUID:
    return dill._GUID(
        Data1=501018480 + int(is_virtual),
        Data2=264,
        Data3=4592,
        Data4=(128, 4, 68, 69, 83, 84, 0, 0),
    )


def _make_fake_device(is_virtual: bool) -> dill.DeviceSummary:
    """Creates a repeatable, faked DeviceSummary."""
    # Data below was generated from a vJoy device.
    guid =  get_fake_device_guid(is_virtual)
    axis_map_array = (dill._AxisMap * 8)()
    for i, (linear_i, axis_i) in enumerate(
        [(1, 1), (2, 2), (3, 3), (4, 6), (5, 7), (6, 8), (7, 0), (8, 0)]
    ):
        axis_map_array[i] = dill._AxisMap(
            linear_index=linear_i, axis_index=axis_i
        )
    return dill.DeviceSummary(
        dill._DeviceSummary(
            device_guid=guid,
            vendor_id=0x1234 if is_virtual else 0x5678,
            product_id=0xBEAD if is_virtual else 0xFACE,
            joystick_id=0 if is_virtual else 1,
            name=b"vJoy Device" if is_virtual else b"pJoy Pro",
            axis_count=6,
            button_count=64,
            hat_count=2,
            axis_map=axis_map_array,
        )
    )


@pytest.fixture(scope="package", autouse=True)
def register_config_options():
    joystick_gremlin.register_config_options()


@pytest.fixture(scope="package", autouse=True)
def joystick_init():
    dill.DILL.init()
    di_stub_devices = {
        0: _make_fake_device(is_virtual=False),
        1: _make_fake_device(is_virtual=True),
    }
    with (
        mock.patch.object(
            dill.DILL,
            dill.DILL.get_device_count.__name__,
            autospec=True,
            return_value=len(di_stub_devices),
        ),
        mock.patch.object(
            dill.DILL,
            dill.DILL.get_device_information_by_index.__name__,
            autospec=True,
            side_effect=di_stub_devices.get,
        ),
        mock.patch.object(
            vjoy,
            vjoy.device_exists.__name__,
            autospec=True,
            side_effect=lambda vjoy_id: vjoy_id == 1,  # A single vJoy device.
        ),
        mock.patch.object(
            vjoy,
            vjoy.axis_count.__name__,
            autospec=True,
            return_value=6,
        ),
        mock.patch.object(
            vjoy,
            vjoy.button_count.__name__,
            autospec=True,
            return_value=64,
        ),
        mock.patch.object(
            vjoy,
            vjoy.hat_count.__name__,
            autospec=True,
            return_value=2,
        ),
        mock.patch.object(
            vjoy,
            vjoy.hat_configuration_valid.__name__,
            autospec=True,
            return_value=True,
        ),
    ):
        gremlin.device_initialization.joystick_devices_initialization()


@pytest.fixture(scope="package", autouse=True)
def terminate_event_listener(request):
    request.addfinalizer(
        lambda: gremlin.event_handler.EventListener().terminate()
    )


@pytest.fixture(scope="package")
def unit_test_dir(test_root_dir: pathlib.Path) -> pathlib.Path:
    """Returns the path for the directory with unit test files."""
    return test_root_dir / "unit"


@pytest.fixture(scope="package")
def xml_dir(unit_test_dir: pathlib.Path) -> pathlib.Path:
    """Returns the path for the directory with XML files for unit tests."""
    return unit_test_dir / "xml"
