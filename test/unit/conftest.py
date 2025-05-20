import sys

import gremlin.device_initialization

sys.path.append(".")

import os.path

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
def xml_dir() -> str:
    """Returns the path for the directory with XML files for unit tests."""
    return os.path.join(os.path.dirname(__file__), "xml")
