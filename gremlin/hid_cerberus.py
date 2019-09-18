import urllib
import os
import json
import re
import gremlin


def _get_web(url):
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.read()
    except urllib.error.URLError:
        return r'["Failed to connect"]'


class HIDCerberus:
    cerberus_API_URL = "http://localhost:/{port}/api/v1/hidguardian/"
    cerberus_API_PORT = 26762
    api_purge_whitelist = "whitelist/purge"
    api_purge_devices = "affected/purge"
    api_whitelist_get = "whitelist/get"
    api_whitelist_add = "whitelist/add/{pid}"
    api_whitelist_rem = "whitelist/remove/{pid}"
    api_devices_get = "affected/get"
    api_devices_add = "affected/add"
    api_devices_rem = "affected/remove"

    def __init__(self): pass

    # TODO: This needs to be a POST command which I'm not yet sure how to handle in urllib
    def add_device(self, vendor_id, product_id): pass

    # TODO: This needs to be a POST command which I'm not yet sure how to handle in urllib
    def remove_device(self, vendor_id, product_id): pass

    def get_device_list(self):
        '''Requests the device list from HID Cerberus
        '''
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
                    gremlin.util.display_error(
                        "Failed to extract vendor and product id for HID Cerberus entry:\n\n{}"
                        .format(device)
                    )
        return device_data

    def add_process(self, process_id):
        '''Requests that HID Cerberus add the PID to its whitelist
        :param process_id PID of the process to be added'''
        API_CALL = (self.cerberus_API_URL + self.api_whitelist_add).format(
            port=self.cerberus_API_PORT,
            pid=process_id
        )
        resp = _get_web(API_CALL)
        # TODO: Do some processing on the response? gremlin.util.log() maybe?

    def remove_process(self, process_id):
        '''Requests that HID Cerberus remove the PID from its whitelist
        :param process_id id of the process to be removed'''
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

    def _create_device_string(self, vendor_id, product_id): pass

    def _get_gremlin_process_ids(self):
        # TODO: use psutil to reach out to OS and get other gremlins?
        # TODO: write our PID to our own location in the registry hive, or a file?
        return [os.getpid()]

    def _synchronize_process(self, process_id): pass
