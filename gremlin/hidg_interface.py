import gremlin.util
import urllib.request
import urllib.error
import re
import json

#####
# Module Globals


#####
# Module functions
def create_device_string(vendor_id, product_id):
    """Returns an appropriately formatted device string.

    :param vendor_id:  the USB vendor id
    :param product_id: the USB product id
    :return: string corresponding to this vendor and product id combination
    """
    return r"HID\VID_{vid:0>4X}&PID_{pid:0>4X}".format(vid=vendor_id, pid=product_id)


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


def mapper_function(func):
    '''
    Helper decorator to make setting up the controller class easier.
    Runs the provider's copy of the function. Call as follows:

    @mapper_function
    def <function name>(): pass
    '''
    def wrapper(self, *args, **kwargs):
        if self._provider is not None:
            getattr(self._provider, func.__name__)(*args, **kwargs)
            return True
        else: return False
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


class HID_Guardian:
    '''Controler class for interacting with HID Guardian. Handles selecting a provider and interacting with it'''
    _provider = None
    _ready = False

    def __init__(self):
        self.set_provider()

    def guardian_available(self):
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

    # pylint: disable=no-method-argument
    # region Device hiding control
    @mapper_function
    def clear_device_list(): pass

    @mapper_function
    def add_device(): pass

    @mapper_function
    def remove_device(): pass

    @mapper_function
    def get_device_list(): pass
    # endregion

    # region Program whitelist control
    @mapper_function
    def clear_process_list(): pass

    @mapper_function
    def add_process(): pass

    @mapper_function
    def remove_process(): pass
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
        API_CALL = cls.generate_API_call(cls.api_devices_purge)
        devices_raw = json.loads(_web_request(API_CALL))
        for device in devices_raw:
            match = split_regex.match(device)
            try:
                device_data.append(int(match.group(1), 16), int(match.group(2), 16))
            except AttributeError:
                # TODO: Match failed, report this (but non-intrusively)
                pass
            except ValueError:
                gremlin.util.display_error(
                    "Failed to extract vendor and product id for HID Cerberus entry:\n\n{}".format(device)
                )
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
    @classmethod
    def is_available(cls):
        # TODO: Actual availabilty code
        return False

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
