# -*- coding: utf-8; -*-

# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from dill import (
    DeviceSummary,
    _DeviceSummary,
)


def test_DeviceSummary_initialisation() -> None:
    c_device_summary = _DeviceSummary()
    c_device_summary.name = b"MOZA R12 Base\x90"
    device_summary = DeviceSummary(data=c_device_summary)

    assert device_summary.name == "MOZA R12 Base"
