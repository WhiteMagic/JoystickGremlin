import sys
sys.path.append(".")

import pathlib

import pytest

import dill

import gremlin.device_initialization
import gremlin.event_handler


@pytest.fixture(scope="package", autouse=True)
def joystick_init():
    dill.DILL.init()
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
