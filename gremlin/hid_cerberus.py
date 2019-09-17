import urllib


def _get_web(url):
    try:
        with urllib.request.urlopen(url) as resp:
            return resp.read()
    except urllib.error.URLError:
        return r'["Failed to connect"]'


class HIDCerberus:
    cerberus_URL = "http://localhost:26762/"
    api_base = "api/v1/hidguardian/"
    api_purge_whitelist = "whitelist/purge"
    api_purge_devices = "affected/purge"
    api_whitelist_get = "whitelist/get"
    api_whitelist_add = "whitelist/add/{}"
    api_whitelist_rem = "whitelist/remove/{}"
    api_devices_get = "affected/get"
    api_devices_add = "affected/add"
    api_devices_rem = "affected/remove"

    def __init__(self): pass

    # TODO: This needs to be a POST command which I'm not yet sure how to handle in urllib
    def add_device(self, vendor_id, product_id): pass

    # TODO: This needs to be a POST command which I'm not yet sure how to handle in urllib
    def remove_device(self, vendor_id, product_id): pass

    def get_device_list(self): pass

    def add_process(self, process_id): pass

    def remove_process(self, process_id): pass

    def clear_process_list(self): pass

    def _create_device_string(self, vendor_id, product_id): pass

    def _get_gremlin_process_ids(self): pass

    def _synchronize_process(self, process_id): pass
