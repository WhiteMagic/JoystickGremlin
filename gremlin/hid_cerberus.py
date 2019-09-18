import urllib.request
from urllib.error import URLError
import os
import json
import re
# import gremlin

def _display_error(*args, **kwargs):
    '''Debug wrapper for gremlin.util.display_error that allows direct import of
    this module (with minimal code rewrite)'''
    # gremlin.util.debug_log(*args, **kwargs)
    print(*args, **kwargs)


def _create_device_string(vendor_id, product_id):
    """Returns an appropriately formatted device string.

    :param vendor_id: the USB vendor id
    :param product_id: the USB product id
    :return: string corresponding to this vendor and product id combination
    """
    return r"HID\VID_{vid:0>4X}&PID_{pid:0>4X}".format(
        vid=vendor_id, pid=product_id
    )


def _get_gremlin_process_ids():
    '''Dummy method for compatibility. Currently only returns own ID.'''
    # TODO: use psutil to reach out to OS and get other gremlins?
    # TODO: write our PID to our own location in the registry hive, or a file?
    return [os.getpid()]


def _synchronize_process(process_id):
    '''Dummy method for compatibility. Does nothing.'''
    pass


def _get_web(url):
    '''GET request sent to url. Returns the content.'''
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.read()
    except URLError:
        return '["ERROR", "Failed to connect"]'


def _post_web(url, data):
    '''POST request sent to the url. Returns the content.'''
    # Crunch the data down into something that the internet will be happy with
    data = urllib.parse.urlencode(data).encode('ascii')
    try:
        with urllib.request.urlopen(url, data) as resp:
            return resp.read()
    except URLError:
        return '["ERROR", "Failed to connect"]'


class HIDCerberus:
    '''Class for interacting with HID Cerberus if installed.
    Designed to mimic the API of gremlin.hid_guardian.HIDGuardian
    '''
    cerberus_API_URL = "http://localhost:{port}/api/v1/hidguardian/"
    cerberus_API_PORT = 26762
    cerberus_listening = False
    api_purge_whitelist = "whitelist/purge"
    api_purge_devices = "affected/purge"
    api_whitelist_get = "whitelist/get"
    api_whitelist_add = "whitelist/add/{pid}"
    api_whitelist_rem = "whitelist/remove/{pid}"
    api_devices_get = "affected/get"
    api_devices_add = "affected/add"
    api_devices_rem = "affected/remove"

    # TODO: Check if HID Cerberus is running when initialized
    # TODO: Check if HID Cerberus is installed?
    def __init__(self):
        resp = _get_web(cerberus_API_URL.format(port=cerberus_API_PORT))
        if "404" in resp:       # The base API URL should return a json object that includes the string "404"
            self.cerberus_listening = True
        elif "ERROR" in resp:   # If ERROR is in the response then we weren't able to connect at all
            _display_error("Unable to connect to HID Cerberus. Please check if it is running/installed.")

    def add_device(self, vendor_id, product_id):
        '''Requests that HID Cerberus add device with vendor_id and product_id'''
        hwidstr = _create_device_string(vendor_id, product_id)
        data = dict(hwids=hwidstr)
        API_CALL = (cerberus_API_URL + api_devices_add).format(
            port=cerberus_API_PORT
        )
        resp = _post_web(API_CALL, data)

    def remove_device(self, vendor_id, product_id):
        '''Requests that HID Cerberus remove device with vendor_id and product_id'''
        hwidstr = _create_device_string(vendor_id, product_id)
        data = dict(hwids=hwidstr)
        API_CALL = (cerberus_API_URL + api_devices_rem).format(
            port=cerberus_API_PORT
        )
        resp = _post_web(API_CALL, data)

    def get_device_list(self):
        '''Requests the device list from HID Cerberus'''
        # Example: ["HID\\VID_0738&PID_2215&MI_00","HID\\VID_044F&PID_0404","HID\\VID_0738&PID_2215&MI_02"]
        API_CALL = (self.cerberus_API_URL + self.api_devices_get).format(
            port=self.cerberus_API_PORT,
        )
        resp = _get_web(API_CALL)

        device_data = []
        split_regex = re.compile(r"HID\\VID_(.{4})&PID_(.{4})")
        # For each device in the list, attempt to regex-match it, then add a tuple of the
        # Vendor ID and Product ID converted to base ten.
        for device in json.loads(resp):
            match = split_regex.match(device)
            if match:
                try:
                    device_data.append((
                        int(match.group(1), 16),
                        int(match.group(2), 16)
                    ))
                except ValueError:
                    _display_error(
                        "Failed to extract vendor and product id for HID Cerberus entry:\n\n{}"
                        .format(device)
                    )
        return device_data

    def add_process(self, process_id):
        '''Requests that HID Cerberus add the PID to its whitelist.

        :param process_id: PID of the process to be added'''
        API_CALL = (self.cerberus_API_URL + self.api_whitelist_add).format(
            port=self.cerberus_API_PORT,
            pid=process_id
        )
        resp = _get_web(API_CALL)
        # TODO: Do some processing on the response? gremlin.util.log() maybe?

    def remove_process(self, process_id):
        '''Requests that HID Cerberus remove the PID from its whitelist

        :param process_id: id of the process to be removed'''
        API_CALL = (self.cerberus_API_URL + self.api_whitelist_rem).format(
            port=self.cerberus_API_PORT,
            pid=process_id
        )
        resp = _get_web(API_CALL)
        # TODO: Do some processing on the response? gremlin.util.log() maybe?

    def clear_process_list(self):
        '''Request HID Cerberus purge its PID whitelist'''
        API_CALL = (self.cerberus_API_URL + self.api_purge_whitelist).format(
            port=self.cerberus_API_PORT
        )
        resp = _get_web(API_CALL)

