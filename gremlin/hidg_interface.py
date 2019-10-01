import gremlin.util
import urllib.request
import urllib.error
import re
import json
import winreg
from functools import wraps
from gremlin.error import HidGuardianError

#####
# Module Globals


#####
# Module functions
def create_device_string(vendor_id, product_id, interface_id=None):
    """Returns an appropriately formatted device string.

    :param vendor_id:  the USB vendor id
    :param product_id: the USB product id
    :return: string corresponding to this vendor and product id combination
    """
    if interface_id is None:
        dev_string = r"HID\VID_{vid:0>4X}&PID_{pid:0>4X}".format(vid=vendor_id, pid=product_id)
    else:
        dev_string = r"HID\VID_{vid:0>4X}&PID_{pid:0>4X}&MI_{iid:0>2X}".format(
            vid=vendor_id, pid=product_id, iid=interface_id
        )
    return dev_string


def _web_request(url, data=None):
    '''Wrapper for urllib.request.urlopen that handles basic setup and error handling.'''
    resp = None

    try:
        if data is not None:
            data = urllib.parse.urlencode(data).encode('ascii')
        with urllib.request.urlopen(url, data=data) as rawresp:
            resp = rawresp.read()
    except urllib.error.HTTPError as error:
        resp = ["ERROR", error.code, error.reason]
    except urllib.error.URLError:
        resp = ["ERROR", "Failed to connect"]
    except TypeError:
        resp = ["ERROR", "Data type not valid"]

    return resp


def _log_error(*args):
    # TODO: Change theis print statement to a gremlin util call before deployment
    print(*args)


def _open_key(sub_key, access=winreg.KEY_READ):
    """Opens a key and returns the handle to it.

    :param sub_key the key to open
    :param access the access rights to use when opening the key
    :return the handle to the opened key
    """
    try:
        return winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
            str(sub_key),
            access=access
        )
    except OSError:
        raise HidGuardianError("Unable to open sub key \"{}\"".format(sub_key))


def _clear_key(handle):
    """Clears a given key of any sub keys. Does NOT check for permission
    to do so before attempting to edit the registry.

    :param handle the handle to the key which should be cleared
    """
    info = winreg.QueryInfoKey(handle)
    # No sub keys which means the parent can delete this now
    if info[0] == 0: return
    # Recursively clear sub keys
    for _ in range(info[0]):
        key = winreg.EnumKey(handle, 0)
        new_hdl = winreg.OpenKey(handle, key)
        _clear_key(new_hdl)
        winreg.DeleteKey(handle, key)


def _read_value(handle, value_name, value_type):
    """Reads a value from a key and returns it.

    :param handle the handle from which to read the value
    :param value_name the name of the value to read
    :param value_type the expected type of the value being read
    :return the read value and its type, returns a value of None if the value
        did not exist
    """
    try:
        data = winreg.QueryValueEx(handle, value_name)
        if data[1] != value_type:
            raise HidGuardianError(
                "Read invalid data type, {} expected {}".format(
                    data[1], value_type
            ))
        return data
    except FileNotFoundError:
        # The particular value doesn't exist, return None instead
        return [None, value_type]
    except PermissionError:
        raise HidGuardianError(
            "Unable to read value \"{}\", insufficient permissions".format(
                value_name
        ))


def _write_value(handle, value_name, data):
    """Writes data to provided handle's value.

    :param handle the key handle to write the value of
    :param value_name name of the value to be written
    :param data data to be written, content and type
    """
    try:
        winreg.SetValueEx(handle, value_name, 0, data[1], data[0])
    except PermissionError:
        raise HidGuardianError(
            "Unable to write value \"{}\", insufficient permissions".format(
                value_name
        ))


def mapper_function(func):
    '''
    Helper decorator to make setting up the controller class easier.
    Runs the provider's copy of the function. Most basic call:

    @mapper_function
    def <function name>(self, return_value): pass
    '''
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        error_no_provider = r"Tried to access HIDG provider despite not having one set.\n\n" +\
                            r"The provider interface should not currently be ready, please file a bug report."
        error_provider_incomplete = "Provider [{}] was unable to supply backing method '{}'"
        if self._ready:
            try:
                return_val = getattr(self._provider, func.__name__)(*args, **kwargs)
                return func(self, return_val)
            except AttributeError:
                if self._provider:
                    _log_error(error_provider_incomplete.format(
                        self._provider.__class__.__name__, func.__name__
                    ))
                else:
                    _log_error(error_no_provider)
        else:
            return func(self, None)
    return wrapper


#####
# Module Classes
class HID_Guardian:
    '''Controler class for interacting with HID Guardian. Handles selecting a provider and interacting with it'''
    _provider = None
    _ready = False
    _blocked_devices = []
    _whitelisted_pids = []

    def __init__(self):
        HIDG_Provider_Cerberus.provider_setup()
        HIDG_Provider_Registry.provider_setup()
        self.set_provider()

    def ready(self):
        return self._ready

    def set_provider(self):
        '''Configure the backing provider, then set the ready state. If no provider is
        available, set state to not ready'''
        if HIDG_Provider_Cerberus.is_available:
            self._provider = HIDG_Provider_Cerberus
            self._ready = True
        elif HIDG_Provider_Registry.is_available:
            self._provider = HIDG_Provider_Registry
            self._ready = True
        else:
            self._ready = False

    # pylint: disable=no-method-argument
    # region Device hiding control
    @mapper_function
    def clear_device_list(self, return_val): pass

    @mapper_function
    def add_device(self, return_val): pass

    @mapper_function
    def remove_device(self, return_val): pass

    @mapper_function
    def get_device_list(self, return_val): pass
    # endregion

    # region Program whitelist control
    @mapper_function
    def clear_process_list(self, return_val): pass

    @mapper_function
    def add_process(self, return_val): pass

    @mapper_function
    def remove_process(self, return_val): pass
    # endregion
    # pylint: enable=no-method-argument


class HIDG_Provider_Cerberus:
    # TODO: We're generating response codes from Cerberus. Pass them to the log files?
    cerberus_API_URL = "http://localhost:{port}/api/v1/hidguardian/"
    cerberus_API_PORT = 26762
    cerberus_listening = False
    api_whitelist_get = "whitelist/get"
    api_whitelist_add = "whitelist/add/{pid}"
    api_whitelist_rem = "whitelist/remove/{pid}"
    api_whitelist_purge = "whitelist/purge"
    api_devices_get = "affected/get"
    api_devices_add = "affected/add"
    api_devices_rem = "affected/remove"
    api_devices_purge = "affected/purge"

    @classmethod
    def generate_API_call(cls, api_action_str, **kwargs):
        return (cls.cerberus_API_URL + api_action_str).format(
            port=cls.cerberus_API_PORT, **kwargs
        )

    @classmethod
    def provider_setup(cls):
        '''Available as part of the standard interface, but this provider needs
        no setup to be used. Should be called anyway in case this changes in
        the future.'''
        pass

    @classmethod
    def is_available(cls):
        resp = _web_request(cls.generate_API_call(""))
        # if Cerberus is running, the server will respond but with a 404 error
        # because we used a bad URL
        return "ERROR" in resp and 404 in resp

    # region Device hiding control
    @classmethod
    def clear_device_list(cls):
        API_CALL = cls.generate_API_call(cls.api_devices_purge)
        _web_request(API_CALL)

    @classmethod
    def add_device(cls, vendor_id, product_id):
        '''Requests that HID Cerberus add device with vendor_id and product_id'''
        data = dict(hwids=create_device_string(vendor_id, product_id))
        API_CALL = cls.generate_API_call(cls.api_devices_add)
        _web_request(API_CALL, data)

    @classmethod
    def remove_device(cls, vendor_id, product_id):
        '''Requests that HID Cerberus remove device with vendor_id and product_id'''
        data = dict(hwids=create_device_string(vendor_id, product_id))
        API_CALL = cls.generate_API_call(cls.api_devices_rem)
        _web_request(API_CALL, data)

    @classmethod
    def get_device_list(cls):
        device_data = []
        split_regex = re.compile(r"HID\\VID_(.{4})&PID_(.{4})")
        API_CALL = cls.generate_API_call(cls.api_devices_get)
        devices_raw = json.loads(_web_request(API_CALL))
        for device in devices_raw:
            match = split_regex.match(device)
            try:
                device_data.append((int(match.group(1), 16), int(match.group(2), 16)))
            except AttributeError:
                # TODO: Match failed, report this (but non-intrusively)
                pass
            except ValueError:
                gremlin.util.display_error(
                    "Failed to extract vendor and product id for HID Cerberus entry:\n\n{}".format(device)
                )
        return device_data
    # endregion

    # region Program whitelist control
    @classmethod
    def clear_process_list(cls):
        '''Request HID Cerberus purge its PID whitelist'''
        API_CALL = cls.generate_API_call(cls.api_whitelist_purge)
        _web_request(API_CALL)

    @classmethod
    def add_process(cls, process_id):
        '''Requests that HID Cerberus add the PID to its whitelist.'''
        API_CALL = cls.generate_API_call(cls.api_whitelist_add, pid=process_id)
        _web_request(API_CALL)

    @classmethod
    def remove_process(cls, process_id):
        '''Requests that HID Cerberus remove the PID from its whitelist'''
        API_CALL = cls.generate_API_call(cls.api_whitelist_rem, pid=process_id)
        _web_request(API_CALL)
    # endregion


class HIDG_Provider_Registry:
    """Interfaces with HidGuardians registry configuration."""
    root_path = r"SYSTEM\CurrentControlSet\Services\HidGuardian\Parameters"
    process_path = r"SYSTEM\CurrentControlSet\Services\HidGuardian\Parameters\Whitelist"
    storage_value = "AffectedDevices"
    _setup_done = False
    _ready = False

    @classmethod
    def is_available(cls):
        return cls._ready

    @classmethod
    def provider_setup(cls):
        '''Sets up the provider for use. Checks for admin rights, if we have admin
        rights, follow that up by trying to create the keys we need. If all of that
        passes the needed checks then we remain in the ready state and set the
        internal _setup_done state.'''
        if not cls._setup_done:
            cls._ready = gremlin.util.is_user_admin()
        else: return
        # This code will only run if we haven't run setup before. This is not
        # in the above if-else in order to reduce indentation level
        if cls._ready:
            try:
                # Ensure we have the needed parameter entries
                with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, cls.root_path) as handle:
                    data = _read_value(
                        handle, cls.storage_value,
                        winreg.REG_MULTI_SZ
                    )
                    if data[0] is None:
                        _write_value(
                            handle, cls.storage_value,
                            [[], winreg.REG_MULTI_SZ]
                        )
                # Ensure we can create per process keys
                with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, cls.process_path):
                    pass
            except OSError:
                cls._ready = False
                raise HidGuardianError("Failed to initialize HidGuardian interface")
        cls._setup_done = True

    # region Device hiding control
    @classmethod
    def clear_device_list(cls): pass

    @classmethod
    def add_device(cls, vendor_id, product_id): pass

    @classmethod
    def remove_device(cls, vendor_id, product_id): pass

    @classmethod
    def get_device_list(cls): pass
    # endregion

    # region Program whitelist control
    @classmethod
    def clear_process_list(cls): pass

    @classmethod
    def add_process(cls, process_id): pass

    @classmethod
    def remove_process(cls, process_id): pass
    # endregion


#####
# Standalone import code/Module setup
if __name__ == "__main__":
    pass
