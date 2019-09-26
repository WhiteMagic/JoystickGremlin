# -*- coding: utf-8; -*-

# Copyright (C) 2015 - 2019 Lionel Ott
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import gremlin.util
import urllib
import urllib.error
import re

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


class HIDG_Provider_Cerberus:
    # TODO: We're generating response codes from Cerberus. Pass them to the log files?
    cerberus_API_URL = "http://localhost:{port}/api/v1/hidguardian/"
    cerberus_API_PORT = 26762
    cerberus_listening = False
    api_whitelist_get = "whitelist/get"
    api_whitelist_add = "whitelist/add/{pid}"
    api_whitelist_rem = "whitelist/remove/{pid}"
    api_purge_whitelist = "whitelist/purge"
    api_devices_get = "affected/get"
    api_devices_add = "affected/add"
    api_devices_rem = "affected/remove"
    api_purge_devices = "affected/purge"

    @classmethod
    def generate_API_call(cls, api_action_str, **kwargs):
        return (cls.cerberus_API_URL + api_action_str).format(
            port=cls.cerberus_API_PORT, **kwargs
        )

    @classmethod
    def is_cerberus_running(cls):
        resp = _web_request(cls.generate_API_call(""))
        # if Cerberus is running, the server will respond but with a 404 error
        # because we used a bad URL
        return "ERROR" in resp and "404" in resp

    #region Device hiding control
    @classmethod
    def clear_device_list(cls):
        pass

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
        pass
    #endregion

    #region Program whitelist control
    @classmethod
    def clear_process_list(cls):
        '''Request HID Cerberus purge its PID whitelist'''
        API_CALL = cls.generate_API_call(cls.api_purge_whitelist)
        _web_request(API_CALL)

    @classmethod
    def add_process(cls, process_id):
        '''Requests that HID Cerberus add the PID to its whitelist.

        :param process_id: PID of the process to be added'''
        API_CALL = cls.generate_API_call(cls.api_whitelist_add, pid=process_id)
        _web_request(API_CALL)

    @classmethod
    def remove_process(cls, process_id):
        '''Requests that HID Cerberus remove the PID from its whitelist

        :param process_id: id of the process to be removed'''
        API_CALL = cls.generate_API_call(cls.api_whitelist_rem, pid=process_id)
        _web_request(API_CALL)
    #endregion


class HIDG_Provider_Registry:
    pass


#####
# Standalone import code/Module setup
if __name__ == "__main__":
    pass

#####
# EVERYTHING BELOW THIS LINE IS OLD CODE

# import re
import winreg

from gremlin.error import HidGuardianError
import gremlin.util


def _open_key(sub_key, access=winreg.KEY_READ):
    """Opens a key and returns the handle to it.

    :param sub_key the key to open
    :param access the access rights to use when opening the key
    :return the handle to the opened key
    """
    try:
        return winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            str(sub_key),
            access=access
        )
    except OSError:
        raise HidGuardianError(
            "Unable to open sub key \"{}\"".format(sub_key)
        )


def _clear_key(handle):
    """Clears a given key of any sub keys.

    :param handle the handle to the key which should be cleared
    """
    info = winreg.QueryInfoKey(handle)

    # No sub keys which means the parent can delete this now
    if info[0] == 0:
        return

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
                    data[1],
                    value_type
                )
            )
        return data
    except FileNotFoundError:
        # The particular value doesn't exist, return None instead
        return [None, value_type]
    except PermissionError:
        raise HidGuardianError(
            "Unable to read value \"{}\", insufficient permissions".format(
                value_name
            )
        )


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
            )
        )


class HidGuardian:

    """Interfaces with HidGuardians registry configuration."""

    root_path = "SYSTEM\CurrentControlSet\Services\HidGuardian\Parameters"
    process_path = "SYSTEM\CurrentControlSet\Services\HidGuardian\Parameters\Whitelist"
    storage_value = "AffectedDevices"

    def __init__(self):
        """Creates a new instance, ensuring proper initial state."""
        self._is_admin = gremlin.util.is_user_admin()
        if not self._is_admin:
            return

        try:
            # Ensure we have the needed parameter entries
            handle = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                HidGuardian.root_path
            )
            data = _read_value(
                handle,
                HidGuardian.storage_value,
                winreg.REG_MULTI_SZ
            )
            if data[0] is None:
                _write_value(
                    handle,
                    HidGuardian.storage_value,
                    [[], winreg.REG_MULTI_SZ]
                )
            handle.Close()

            # Ensure we can create per process keys
            handle = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                HidGuardian.process_path
            )
            handle.Close()
        except OSError:
            raise HidGuardianError("Failed to initialize HidGuardian interface")

    def add_device(self, vendor_id, product_id):
        """Adds a new device to the list of devices managed by HidGuardian.

        :param vendor_id the USB vendor id
        :param product_id the USB product id
        """
        if not self._is_admin:
            return

        # Add device to the list of devices that HidGuardian is intercepting
        handle = _open_key(HidGuardian.root_path, winreg.KEY_ALL_ACCESS)
        data = _read_value(
            handle,
            HidGuardian.storage_value,
            winreg.REG_MULTI_SZ
        )

        device_string = self._create_device_string(vendor_id, product_id)
        if data[0] is None:
            data[0] = []
        if device_string not in data[0]:
            data[0].append(device_string)
            _write_value(handle, HidGuardian.storage_value, data)

        # Update device list for any existing Gremlin process keys
        for pid in self._get_gremlin_process_ids():
            self._synchronize_process(pid)

    def remove_device(self, vendor_id, product_id):
        """Removes a device from the list of devices managed by HidGuardian

        :param vendor_id the USB vendor id
        :param product_id the USB product id
        """
        if not self._is_admin:
            return

        # Get list of current devices and remove the specified one from it
        handle = _open_key(HidGuardian.root_path, winreg.KEY_ALL_ACCESS)
        data = winreg.QueryValueEx(handle, HidGuardian.storage_value)

        device_string = self._create_device_string(vendor_id, product_id)
        if device_string in data[0]:
            data[0].remove(device_string)
            _write_value(handle, HidGuardian.storage_value, data)

        # Update device list for any existing Gremlin process keys
        for pid in self._get_gremlin_process_ids():
            self._synchronize_process(pid)

    def get_device_list(self):
        """Returns the list of devices handled by HidGuardian.

        The ids are represented as integers in base 10 as opposed to hex, as
        Gremlin uses base 10 to represent them.

        :return list of vendor and product id of devices managed by HidGuardian
        """
        if not self._is_admin:
            return

        # Get list of handled devices
        root_handle = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            HidGuardian.root_path
        )
        data = _read_value(
            root_handle,
            HidGuardian.storage_value,
            winreg.REG_MULTI_SZ
        )

        # Process each entry to extract vendor and product id
        device_data = []
        split_regex = re.compile("HID\\\\VID_(.{4})&PID_(.{4})")
        for entry in data[0]:
            match = split_regex.match(entry)
            if match:
                try:
                    device_data.append((
                        int(match.group(1), 16),
                        int(match.group(2), 16)
                    ))
                except ValueError:
                    gremlin.util.display_error(
                        "Failed to extract vendor and product id for HidGuardian entry:\n\n{}"
                            .format(entry)
                    )


        return device_data

    def add_process(self, process_id):
        """Adds a new process.

        :param process_id id of the process to add
        """
        if not self._is_admin:
            return

        # Remove any existing processes belonging to Gremlin instances
        for pid in self._get_gremlin_process_ids():
            self.remove_process(pid)

        # Ensure the process key exists and write the identifying value
        handle = winreg.CreateKey(
            winreg.HKEY_LOCAL_MACHINE,
            "{}\{}".format(HidGuardian.process_path, process_id)
        )
        winreg.SetValueEx(handle, "Joystick Gremlin", 0, winreg.REG_DWORD, 1)
        self._synchronize_process(process_id)

    def remove_process(self, process_id):
        """Removes the key corresponding to the provided process.

        :param process_id id of the process to be removed
        """
        if not self._is_admin:
            return

        try:
            handle = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                HidGuardian.process_path
            )
            key_handle = winreg.OpenKey(handle, str(process_id))
            _clear_key(key_handle)
            winreg.DeleteKey(handle, str(process_id))
        except OSError:
            # OSError is thrown if the key doesn't exist, which means there is
            # nothing for us to remove
            pass

    def clear_process_list(self):
        if not self._is_admin:
            return

        _clear_key(_open_key(HidGuardian.process_path))

    def _create_device_string(self, vendor_id, product_id):
        """Returns an appropriately formatted device string.

        :param vendor_id the USB vendor id
        :param product_id the USB product id
        :return string corresponding to this vendor and product id combination
        """
        return "HID\\VID_{:0>4s}&PID_{:0>4s}".format(
            hex(vendor_id)[2:],
            hex(product_id)[2:]
        )

    def _get_gremlin_process_ids(self):
        """Returns all handles of processes associated with Gremlin.

        :return list of handles associated with Gremlin processes
        """
        if not self._is_admin:
            return

        try:
            handle = _open_key(HidGuardian.process_path)

            # Walk all sub keys and check each if they contain the value that
            # flags them as being from Gremlin
            info = winreg.QueryInfoKey(handle)

            # Check each sub key
            gremlin_pids = []
            for i in range(info[0]):
                sub_key = winreg.EnumKey(handle, i)
                sub_handle = _open_key("{}\{}".format(
                    HidGuardian.process_path,
                    sub_key
                ))
                winreg.OpenKey(handle, sub_key)
                sub_info = winreg.QueryInfoKey(sub_handle)
                # Check each sub key value
                for j in range(sub_info[1]):
                    value_info = winreg.EnumValue(sub_handle, j)
                    if value_info[0] == "Joystick Gremlin":
                        gremlin_pids.append(sub_key)

            return gremlin_pids
        except OSError:
            raise HidGuardianError("Failed to retrieve Gremlin process handle")

    def _synchronize_process(self, process_id):
        """Synchronizes the managed devices to the provided process.

        :param process_id id of the process to synchronize the device data to
        """
        if not self._is_admin:
            return

        # Get data about devices handled by HidGuardian
        root_handle = _open_key(HidGuardian.root_path)
        data = _read_value(
            root_handle,
            HidGuardian.storage_value,
            winreg.REG_MULTI_SZ
        )

        # Write the same data to the process exemption list
        handle = _open_key(
            "{}\{}".format(HidGuardian.process_path, process_id),
            access=winreg.KEY_WRITE
        )
        _write_value(handle, HidGuardian.storage_value, data)
