# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

"""Abstract base class that all vjoy platform backends must implement."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AbstractVJoyBackend(ABC):
    """Contract for vjoy platform backends (virtual joystick output).

    Each backend is responsible for:
    - reporting whether the virtual joystick driver is available,
    - managing the lifecycle of virtual device instances (acquire/relinquish),
    - answering capability queries (axis count, button count, etc.),
    - accepting input values and forwarding them to the virtual device.

    All values crossing this interface are plain Python types (int, bool, str)
    — no ctypes structs are shared between layers.
    """

    # ------------------------------------------------------------------
    # Driver info
    # ------------------------------------------------------------------

    @abstractmethod
    def vjoy_enabled(self) -> bool:
        """Return True if the virtual joystick driver is available."""

    @abstractmethod
    def get_version(self) -> int:
        """Return the driver version as an integer (e.g. 0x218 = 2.1.8)."""

    def get_product_string(self) -> str:
        """Return the driver product string (Windows only, empty elsewhere)."""
        return ""

    def get_manufacturer_string(self) -> str:
        """Return the driver manufacturer string (Windows only, empty elsewhere)."""
        return ""

    def get_serial_number_string(self) -> str:
        """Return the driver serial number string (Windows only, empty elsewhere)."""
        return ""

    # ------------------------------------------------------------------
    # Device status
    # ------------------------------------------------------------------

    @abstractmethod
    def get_vjd_status(self, vjoy_id: int) -> int:
        """Return the raw VJoyState int value for the given device id."""

    @abstractmethod
    def get_owner_pid(self, vjoy_id: int) -> int:
        """Return the PID of the process owning the device, or -1 if free."""

    # ------------------------------------------------------------------
    # Device acquisition
    # ------------------------------------------------------------------

    @abstractmethod
    def acquire_vjd(self, vjoy_id: int) -> bool:
        """Acquire exclusive ownership of the given device. Return True on success."""

    @abstractmethod
    def relinquish_vjd(self, vjoy_id: int) -> None:
        """Release exclusive ownership of the given device."""

    # ------------------------------------------------------------------
    # Device capabilities
    # ------------------------------------------------------------------

    @abstractmethod
    def get_vjd_button_number(self, vjoy_id: int) -> int:
        """Return the number of buttons on the given device."""

    @abstractmethod
    def get_vjd_disc_pov_number(self, vjoy_id: int) -> int:
        """Return the number of discrete POV hats on the given device."""

    @abstractmethod
    def get_vjd_cont_pov_number(self, vjoy_id: int) -> int:
        """Return the number of continuous POV hats on the given device."""

    @abstractmethod
    def get_vjd_axis_exist(self, vjoy_id: int, axis_id: int) -> int:
        """Return non-zero if the given axis exists on the given device."""

    @abstractmethod
    def get_vjd_axis_max(self, vjoy_id: int, axis_id: int) -> int:
        """Return the maximum raw value for the given axis (e.g. 32767)."""

    @abstractmethod
    def get_vjd_axis_min(self, vjoy_id: int, axis_id: int) -> int:
        """Return the minimum raw value for the given axis (e.g. 0 or -32768)."""

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    @abstractmethod
    def reset_vjd(self, vjoy_id: int) -> bool:
        """Reset all inputs on the given device to neutral. Return True on success."""

    @abstractmethod
    def reset_all(self) -> None:
        """Reset all managed virtual devices to neutral."""

    @abstractmethod
    def reset_buttons(self, vjoy_id: int) -> bool:
        """Reset all buttons on the given device. Return True on success."""

    @abstractmethod
    def reset_povs(self, vjoy_id: int) -> bool:
        """Reset all POV hats on the given device. Return True on success."""

    # ------------------------------------------------------------------
    # Set values
    # ------------------------------------------------------------------

    @abstractmethod
    def set_axis(self, value: int, vjoy_id: int, axis_id: int) -> bool:
        """Set the raw axis value. Return True on success."""

    @abstractmethod
    def set_btn(self, pressed: bool, vjoy_id: int, btn_id: int) -> bool:
        """Set button state (True = pressed). Return True on success."""

    @abstractmethod
    def set_disc_pov(self, direction: int, vjoy_id: int, hat_id: int) -> bool:
        """Set discrete POV direction (0=N, 1=E, 2=S, 3=W, -1=center).
        Return True on success."""

    @abstractmethod
    def set_cont_pov(self, degrees: int, vjoy_id: int, hat_id: int) -> bool:
        """Set continuous POV direction in DirectInput hundredths-of-degrees
        (0=N, 9000=E, 18000=S, 27000=W, -1=center). Return True on success."""
