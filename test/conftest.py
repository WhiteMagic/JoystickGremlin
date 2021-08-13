import sys
sys.path.append(".")

import pytest

import dill

import gremlin.event_handler
import gremlin.joystick_handling


@pytest.fixture(scope="session", autouse=True)
def joystick_init():
    dill.DILL.init()
    gremlin.joystick_handling.joystick_devices_initialization()


@pytest.fixture(scope="session", autouse=True)
def terminate_event_listener(request):
    request.addfinalizer(
        lambda: gremlin.event_handler.EventListener().terminate()
    )