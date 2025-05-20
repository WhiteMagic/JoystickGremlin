import sys

import gremlin.device_initialization

sys.path.append(".")

import pytest

import dill

import gremlin.device_initialization
import gremlin.event_handler


@pytest.fixture(scope="session", autouse=True)
def joystick_init():
    dill.DILL.init()
    gremlin.device_initialization.joystick_devices_initialization()


@pytest.fixture(scope="session", autouse=True)
def terminate_event_listener(request):
    request.addfinalizer(
        lambda: gremlin.event_handler.EventListener().terminate()
    )