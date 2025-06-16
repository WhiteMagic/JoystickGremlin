import logging
import threading

import linput
from gremlin import error, util


_joystick_devices = []
_joystick_init_lock = threading.Lock()


def joystick_devices_initialization():
    """Initializes joystick device information.

    This function retrieves information about various joystick devices and
    associates them and collates their information as required.

    For Linux, this simply gets the current list of devices from the
    linput device manager.
    """
    global _joystick_devices, _joystick_init_lock

    _joystick_init_lock.acquire()

    syslog = logging.getLogger("system")
    syslog.info("Initializing joystick devices")

    try:
        # Get all devices from Linux input manager
        devices = linput.get_joystick_devices()
        syslog.debug(f"{len(devices)} joysticks detected")

        # Compare existing versus observed devices and only proceed if there
        # is a change to avoid unnecessary work.
        device_added = False
        device_removed = False
        for new_dev in devices:
            if new_dev not in _joystick_devices:
                device_added = True
                syslog.debug(f"Added: name={new_dev.name} path={new_dev.device_path}")
        for old_dev in _joystick_devices:
            if old_dev not in devices:
                device_removed = True
                syslog.debug(f"Removed: name={old_dev.name} path={old_dev.device_path}")

        # Update device list
        _joystick_devices = devices
        
        if device_added or device_removed:
            syslog.info(f"Device list updated: {len(_joystick_devices)} devices available")

    except Exception as e:
        syslog.error(f"Error during device initialization: {e}")
        _joystick_devices = []
    
    _joystick_init_lock.release()


def joystick_devices() -> list[linput.DeviceSummary]:
    """Returns the list of joystick like devices.

    Returns:
        List containing information about all joystick devices
    """
    return _joystick_devices


def vjoy_devices() -> list[linput.DeviceSummary]:
    """Returns the list of virtual devices.

    Returns:
        List of virtual devices
    """
    return [dev for dev in _joystick_devices if dev.is_virtual]


def physical_devices() -> list[linput.DeviceSummary]:
    """Returns the list of physical devices.

    Returns:
        List of physical devices
    """
    return [dev for dev in _joystick_devices if not dev.is_virtual]
