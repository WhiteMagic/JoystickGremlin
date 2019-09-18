import urllib


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

    def get_device_list(self): pass

    def add_process(self, process_id):
        '''Requests that HID Cerberus add the PID to its whitelist
        :param process_id PID of the process to be added'''
        API_CALL = (self.cerberus_API_URL + self.api_whitelist_add).format(
            port = self.cerberus_API_PORT,
            pid = process_id
        )
        resp = _get_web(API_CALL)
        # TODO: Do some processing on the response? gremlin.util.log() maybe?

    def remove_process(self, process_id):
        '''Requests that HID Cerberus remove the PID from its whitelist
        :param process_id id of the process to be removed'''
        API_CALL = (self.cerberus_API_URL + self.api_whitelist_rem).format(
            port = self.cerberus_API_PORT,
            pid = process_id
        )
        resp = _get_web(API_CALL)
        # TODO: Do some processing on the response? gremlin.util.log() maybe?

    def clear_process_list(self):
        '''Request HID Cerberus purge its PID whitelist'''
        API_CALL = (self.cerberus_API_URL + self.api_purge_whitelist).format(
            port = self.cerberus_API_PORT
        )
        resp = _get_web(API_CALL)

    def _create_device_string(self, vendor_id, product_id): pass

    def _get_gremlin_process_ids(self): pass

    def _synchronize_process(self, process_id): pass
