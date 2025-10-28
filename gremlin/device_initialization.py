import logging
import threading

import dill
from gremlin import error, util
from vjoy.vjoy import VJoyProxy
from vjoy import vjoy


_joystick_devices = []
_joystick_init_lock = threading.Lock()


def joystick_devices_initialization() -> None:
    """Initializes joystick device information.

    This function retrieves information about various joystick devices and
    associates them and collates their information as required.

    Amongst other things this also ensures that each vJoy device has a correct
    windows id assigned to it.
    """
    global _joystick_devices, _joystick_init_lock

    _joystick_init_lock.acquire()

    syslog = logging.getLogger("system")
    syslog.info("Initializing joystick devices")
    syslog.debug(
        "{:d} joysticks detected".format(dill.DILL.get_device_count())
    )

    # Process all connected devices in order to properly initialize the
    # device registry
    devices = []
    for i in range(dill.DILL.get_device_count()):
        info = dill.DILL.get_device_information_by_index(i)
        devices.append(info)

    # Process all devices again to detect those that have been added and those
    # that have been removed since the last time this function ran.

    # Compare existing versus observed devices and only proceed if there
    # is a change to avoid unnecessary work.
    device_added = False
    device_removed = False
    for new_dev in devices:
        if new_dev not in _joystick_devices:
            device_added = True
            syslog.debug("Added: name={} guid={}".format(
                new_dev.name,
                new_dev.device_guid
            ))
    for old_dev in _joystick_devices:
        if old_dev not in devices:
            device_removed = True
            syslog.debug("Removed: name={} guid={}".format(
                old_dev.name,
                old_dev.device_guid
            ))

    # Terminate if no change occurred
    if not device_added and not device_removed:
        _joystick_init_lock.release()
        return

    # In order to associate vJoy devices and their ids correctly with SDL
    # device ids a hash is constructed from the number of axes, buttons, and
    # hats. This information is used to attempt to find unambiguous mappings
    # between vJoy and SDL devices. If this is not possible Gremlin will
    # terminate as this is a non-recoverable error.

    vjoy_lookup = {}
    for dev in [dev for dev in devices if dev.is_virtual]:
        hash_value = (dev.axis_count, dev.button_count, dev.hat_count)
        syslog.debug(
            "vJoy guid={}: {}".format(dev.device_guid, hash_value)
        )

        # Only unique combinations of axes, buttons, and hats are allowed
        # for vJoy devices
        if hash_value in vjoy_lookup:
            raise error.GremlinError(
                "Indistinguishable vJoy devices present.\n\n"
                "vJoy devices have to differ in the number of "
                "(at least one of) axes, buttons, or hats in order to work "
                "properly with Joystick Gremlin."
            )

        vjoy_lookup[hash_value] = dev

    # Query all vJoy devices in sequence until all have been processed and
    # their matching SDL counterparts have been found.
    vjoy_proxy = VJoyProxy()
    should_terminate = False
    for i in range(1, 17):
        # Only process devices that actually exist
        if not vjoy.device_exists(i):
            continue

        # Compute a hash for the vJoy device and match it against the SDL
        # device hashes
        hash_value = (
            vjoy.axis_count(i),
            vjoy.button_count(i),
            vjoy.hat_count(i)
        )

        if not vjoy.hat_configuration_valid(i):
            error_string = "vJoy id {:d}: Hats are set to discrete but have " \
                           "to be set as continuous.".format(i)
            syslog.debug(error_string)
            util.display_error(error_string)

        # As we are ensured that no duplicate vJoy devices exist from
        # the previous step we can directly link the SDL and vJoy device
        if hash_value in vjoy_lookup:
            vjoy_lookup[hash_value].set_vjoy_id(i)
            syslog.debug("vjoy id {:d}: {} - MATCH".format(i, hash_value))
        else:
            should_terminate = True
            syslog.debug(
                "vjoy id {:d}: {} - ERROR - vJoy device exists "
                "but DILL does not see it".format(i, hash_value)
            )

        # If the device can be acquired, configure the mapping from
        # vJoy axis id, which may not be sequential, to the
        # sequential SDL axis id
        if hash_value in vjoy_lookup:
            try:
                vjoy_dev = vjoy_proxy[i]
            except error.VJoyError as e:
                syslog.debug("vJoy id {:} can't be acquired".format(i))

    if should_terminate:
        raise error.GremlinError(
            "Unable to match vJoy devices to windows devices."
        )

    # Reset all devices so we don't hog the ones we aren't actually using
    vjoy_proxy.reset()

    # Update device list which will be used when queries for joystick devices
    # are made. Order the devices such that vJoy devices are last and the
    # physical devices are ordered by name.
    sorted_devices = sorted(
        [dev for dev in devices if not dev.is_virtual],
        key=lambda x: x.name
    )
    sorted_devices.extend(sorted(
        [dev for dev in devices if dev.is_virtual],
        key=lambda x: x.vjoy_id
    ))

    _joystick_devices = sorted_devices
    _joystick_init_lock.release()


def joystick_devices() -> list[dill.DeviceSummary]:
    """Returns the list of joystick like devices.

    Returns:
        List containing information about all joystick devices
    """
    return _joystick_devices


def vjoy_devices() -> list[dill.DeviceSummary]:
    """Returns the list of vJoy devices.

    Returns:
        List of vJoy devices
    """
    return [dev for dev in _joystick_devices if dev.is_virtual]


def physical_devices() -> list[dill.DeviceSummary]:
    """Returns the list of physical devices.

    Returns:
        List of physical devices
    """
    return [dev for dev in _joystick_devices if not dev.is_virtual]
