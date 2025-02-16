from dill import _DeviceSummary, DeviceSummary


def test_DeviceSummary_initialisation():
    c_device_summary = _DeviceSummary()
    c_device_summary.name = b'MOZA R12 Base\x90'
    device_summary = DeviceSummary(data=c_device_summary)

    assert device_summary.name == "MOZA R12 Base"
