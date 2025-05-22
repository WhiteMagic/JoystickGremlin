import sys
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


def _make_fake_device(is_virtual: bool) -> dill.DeviceSummary:
    """Creates a repeatable, faked DeviceSummary."""
    # Data below was generated from a vJoy device.
    guid = dill._GUID(
        Data1=501018480 + int(is_virtual),
        Data2=264,
        Data3=4592,
        Data4=(128, 4, 68, 69, 83, 84, 0, 0),
    )
    axis_map_array = (dill._AxisMap * 8)()
    for i in range(8):
        axis_map_array[i] = axis_map = dill._AxisMap(
            linear_index=i + 1, axis_index=i + 1
        )
    return dill.DeviceSummary(
        dill._DeviceSummary(
            device_guid=guid,
            vendor_id=0x1234 if is_virtual else 0x5678,
            product_id=0xBEAD if is_virtual else 0xFACE,
            joystick_id=0 if is_virtual else 1,
            name=b"vJoy Device" if is_virtual else b"pJoy Pro",
            axis_count=8,
            button_count=128,
            hat_count=4,
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
            return_value=8,
        ),
        mock.patch.object(
            vjoy,
            vjoy.button_count.__name__,
            autospec=True,
            return_value=128,
        ),
        mock.patch.object(
            vjoy,
            vjoy.hat_count.__name__,
            autospec=True,
            return_value=4,
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
def xml_dir() -> pathlib.Path:
    """Returns the path for the directory with XML files for unit tests."""
    return pathlib.Path(__file__).parent / "xml"
